import logging

from django.utils.translation import get_language

from speedy.core.base.utils import get_age_ranges_match
from speedy.core.base.models import BaseManager
from speedy.core.accounts.models import User
from speedy.core.blocks.models import Block

logger = logging.getLogger(__name__)


class SiteProfileManager(BaseManager):
    def get_matches(self, user_profile):
        # Same function as user_profile.get_matching_rank(other_profile=user.speedy_match_profile), but more optimized.
        def get_rank():
            if (user.pk == other_user.pk):
                return self.model.RANK_0
            if (other_user.gender not in user_profile.gender_to_match):
                return self.model.RANK_0
            if (user.gender not in other_user.speedy_match_profile.gender_to_match):
                return self.model.RANK_0
            if (not (user_profile.min_age_to_match <= other_user.get_age() <= user_profile.max_age_to_match)):
                return self.model.RANK_0
            if (not (other_user.speedy_match_profile.min_age_to_match <= user.get_age() <= other_user.speedy_match_profile.max_age_to_match)):
                return self.model.RANK_0
            if (not ((self.model.settings.MIN_HEIGHT_TO_MATCH <= user.speedy_match_profile.height <= self.model.settings.MAX_HEIGHT_TO_MATCH) and (self.model.settings.MIN_HEIGHT_TO_MATCH <= other_user.speedy_match_profile.height <= self.model.settings.MAX_HEIGHT_TO_MATCH))):
                return self.model.RANK_0
            if (user.speedy_match_profile.not_allowed_to_use_speedy_match or other_user.speedy_match_profile.not_allowed_to_use_speedy_match):
                return self.model.RANK_0
            if (other_user.pk in blocked_users_ids):
                return self.model.RANK_0
            if (other_user.pk in blocking_users_ids):
                return self.model.RANK_0
            other_diet_rank = other_user.speedy_match_profile.diet_match.get(str(user.diet), self.model.RANK_0)
            other_smoking_status_rank = other_user.speedy_match_profile.smoking_status_match.get(str(user.smoking_status), self.model.RANK_0)
            other_relationship_status_rank = other_user.speedy_match_profile.relationship_status_match.get(str(user.relationship_status), self.model.RANK_0)
            other_user_rank = min([other_diet_rank, other_smoking_status_rank, other_relationship_status_rank])
            if (other_user_rank == self.model.RANK_0):
                return self.model.RANK_0
            diet_rank = user_profile.diet_match.get(str(other_user.diet), self.model.RANK_0)
            smoking_status_rank = user_profile.smoking_status_match.get(str(other_user.smoking_status), self.model.RANK_0)
            relationship_status_rank = user_profile.relationship_status_match.get(str(other_user.relationship_status), self.model.RANK_0)
            rank = min([diet_rank, smoking_status_rank, relationship_status_rank])
            return rank

        user = user_profile.user
        user_profile._set_values_to_match()
        age_ranges = get_age_ranges_match(min_age=user_profile.min_age_to_match, max_age=user_profile.max_age_to_match)
        language_code = get_language()
        qs = User.objects.active(
            gender__in=user_profile.gender_to_match,
            diet__in=user_profile.diet_to_match,
            smoking_status__in=user_profile.smoking_status_to_match,
            relationship_status__in=user_profile.relationship_status_to_match,
            speedy_match_site_profile__gender_to_match__contains=[user.gender],
            speedy_match_site_profile__diet_to_match__contains=[user.diet],
            speedy_match_site_profile__smoking_status_to_match__contains=[user.smoking_status],
            speedy_match_site_profile__relationship_status_to_match__contains=[user.relationship_status],
            date_of_birth__range=age_ranges,
            speedy_match_site_profile__min_age_to_match__lte=user.get_age(),
            speedy_match_site_profile__max_age_to_match__gte=user.get_age(),
            speedy_match_site_profile__height__range=(self.model.settings.MIN_HEIGHT_TO_MATCH, self.model.settings.MAX_HEIGHT_TO_MATCH),
            speedy_match_site_profile__not_allowed_to_use_speedy_match=False,
            speedy_match_site_profile__active_languages__contains=[language_code],
        ).exclude(pk=user_profile.user_id).order_by('-speedy_match_site_profile__last_visit')
        user_list = qs[:2000]
        blocked_users_ids = Block.objects.filter(blocker__pk=user.pk).values_list('blocked_id', flat=True)
        blocking_users_ids = Block.objects.filter(blocked__pk=user.pk).values_list('blocker_id', flat=True)
        # matches_list = [user for user in user_list if ((user.speedy_match_profile.is_active) and (user_profile.get_matching_rank(other_profile=user.speedy_match_profile) > self.model.RANK_0))]
        matches_list = []
        for other_user in user_list:
            other_user.speedy_match_profile.rank = get_rank()
            if ((other_user.speedy_match_profile.is_active) and (other_user.speedy_match_profile.rank > self.model.RANK_0)):
                matches_list.append(other_user)
        matches_list = sorted(matches_list, key=lambda user: (user.speedy_match_profile.rank, user.speedy_match_profile.last_visit), reverse=True)
        matches_list = matches_list[:720]
        # Save number of matches in this language in user's profile.
        user_profile.number_of_matches = len(matches_list)
        user_profile.save()
        logger.debug("SiteProfileManager::get_matches:user={user}, language_code={language_code}, number_of_matches={number_of_matches}".format(
            user=user,
            language_code=language_code,
            number_of_matches=len(matches_list),
        ))
        if ((not (self.model.settings.MIN_HEIGHT_TO_MATCH <= user_profile.height <= self.model.settings.MAX_HEIGHT_TO_MATCH)) or (user_profile.height <= 85) or (user_profile.not_allowed_to_use_speedy_match)):
            logger.warning("SiteProfileManager::get_matches:user={user}, language_code={language_code}, number_of_matches={number_of_matches}, height={height}, not_allowed_to_use_speedy_match={not_allowed_to_use_speedy_match}".format(
                user=user,
                language_code=language_code,
                number_of_matches=len(matches_list),
                height=user_profile.height,
                not_allowed_to_use_speedy_match=user_profile.not_allowed_to_use_speedy_match,
            ))
        return matches_list


