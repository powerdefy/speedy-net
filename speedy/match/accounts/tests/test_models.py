from datetime import date
import itertools

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.utils import DataError

from speedy.core.base.test import TestCase, only_on_speedy_match
from speedy.core.accounts.tests.test_mixins import ErrorsMixin
from ..models import SiteProfile as SpeedyMatchSiteProfile
from speedy.match.accounts import utils, validators
from speedy.core.accounts.models import User
from speedy.core.accounts.tests.test_factories import DefaultUserFactory, ActiveUserFactory
from speedy.core.uploads.tests.test_factories import UserImageFactory


@only_on_speedy_match
class SpeedyMatchSiteProfileTestCase(ErrorsMixin, TestCase):
    _none_list = [None]
    _empty_string_list = [""]
    _empty_values_to_test = _none_list + _empty_string_list
    _non_int_string_values_to_test = ["Tel Aviv.", "One boy.", "Yes.", "Hi!"]
    _valid_string_values_to_test = ["1"] + _non_int_string_values_to_test

    def get_default_user_1(self):
        user = DefaultUserFactory(first_name='Jesse', last_name='Pinkman', slug='jesse-pinkman', date_of_birth=date(year=1978, month=9, day=12), gender=User.GENDER_FEMALE)
        user.diet = User.DIET_VEGAN
        user.save_user_and_profile()
        return user

    def get_default_user_2(self):
        user = ActiveUserFactory(first_name='Jesse', last_name='Pinkman', slug='jesse-pinkman', date_of_birth=date(year=1978, month=9, day=12), gender=User.GENDER_FEMALE)
        user.diet = User.DIET_VEGETARIAN
        user.save_user_and_profile()
        return user

    def get_min_max_age_to_match_default_test_settings(self):
        test_settings = {
            "field_name": 'min_max_age_to_match',
            "expected_step": 7,
            "expected_error_message_min_age_match_and_max_age_match_valid": "Maximal age to match can't be less than minimal age to match.",
            "expected_error_message_min_age_match_invalid": 'Minimal age to match must be from 0 to 180 years.',
            "expected_error_message_max_age_match_invalid": 'Maximal age to match must be from 0 to 180 years.',
            "expected_error_messages_min_age_match_and_max_age_match_valid": ['["Maximal age to match can\'t be less than minimal age to match."]'],
            "expected_error_messages_min_age_match_and_max_age_match_invalid": ["['Minimal age to match must be from 0 to 180 years.']", "['Maximal age to match must be from 0 to 180 years.']"],
        }
        return test_settings

    def get_diet_match_default_test_settings(self):
        test_settings = {
            "field_name": 'diet_match',
            "expected_step": 8,
            "expected_error_message_keys_and_ranks_invalid": 'Please select diet match.',
            "expected_error_messages_keys_and_ranks_invalid": ["['Please select diet match.']"],
            "expected_error_message_max_rank_invalid": 'At least one diet match option should be 5 hearts.',
            "expected_error_messages_max_rank_invalid": ["['At least one diet match option should be 5 hearts.']"],
        }
        return test_settings

    def get_smoking_status_match_default_test_settings(self):
        test_settings = {
            "field_name": 'smoking_status_match',
            "expected_step": 8,
            "expected_error_message_keys_and_ranks_invalid": 'Please select smoking status match.',
            "expected_error_messages_keys_and_ranks_invalid": ["['Please select smoking status match.']"],
            "expected_error_message_max_rank_invalid": 'At least one smoking status match option should be 5 hearts.',
            "expected_error_messages_max_rank_invalid": ["['At least one smoking status match option should be 5 hearts.']"],
        }
        return test_settings

    def get_marital_status_match_default_test_settings(self):
        test_settings = {
            "field_name": 'marital_status_match',
            "expected_step": 9,
            "expected_error_message_keys_and_ranks_invalid": 'Please select marital status match.',
            "expected_error_messages_keys_and_ranks_invalid": ["['Please select marital status match.']"],
            "expected_error_message_max_rank_invalid": 'At least one marital status match option should be 5 hearts.',
            "expected_error_messages_max_rank_invalid": ["['At least one marital status match option should be 5 hearts.']"],
        }
        return test_settings

    def get_field_default_value(self, field_name):
        if (field_name in ['diet_match']):
            default_value = SpeedyMatchSiteProfile.diet_match_default()
        elif (field_name in ['smoking_status_match']):
            default_value = SpeedyMatchSiteProfile.smoking_status_match_default()
        elif (field_name in ['marital_status_match']):
            default_value = SpeedyMatchSiteProfile.marital_status_match_default()
        else:
            raise Exception("Unexpected: field_name={}".format(field_name))
        return default_value

    def validate_all_user_values(self, user):
        all_fields = ['photo', 'profile_description', 'city', 'children', 'more_children', 'match_description', 'height', 'diet', 'smoking_status', 'marital_status', 'gender_to_match', 'min_age_match', 'max_age_match', 'min_max_age_to_match', 'diet_match', 'smoking_status_match', 'marital_status_match']
        _all_fields = []
        for step in utils.get_steps_range():
            fields = utils.get_step_fields_to_validate(step=step)
            _all_fields.extend(fields)
        self.assertListEqual(list1=sorted(all_fields), list2=sorted(_all_fields))
        self.assertSetEqual(set1=set(all_fields), set2=set(_all_fields))
        for field_name in all_fields:
            utils.validate_field(field_name=field_name, user=user)

    def assert_list_2_contains_all_elements_in_list_1(self, list_1, list_2):
        for value in list_1:
            self.assertIn(member=value, container=list_2)

    def assert_list_2_doesnt_contain_elements_in_list_1(self, list_1, list_2):
        for value in list_1:
            self.assertNotIn(member=value, container=list_2)

    def assert_valid_values_ok(self, values_to_test, valid_values_to_assign, valid_values_to_save, valid_values, invalid_values):
        self.assertIsNotNone(obj=values_to_test)
        self.assertIsNotNone(obj=valid_values_to_assign)
        self.assertIsNotNone(obj=valid_values_to_save)
        self.assertIsNotNone(obj=valid_values)
        self.assertIsNotNone(obj=invalid_values)
        if (isinstance(values_to_test, range)):
            values_to_test = list(values_to_test)
        if (isinstance(valid_values_to_assign, range)):
            valid_values_to_assign = list(valid_values_to_assign)
        if (isinstance(valid_values_to_save, range)):
            valid_values_to_save = list(valid_values_to_save)
        if (isinstance(valid_values, range)):
            valid_values = list(valid_values)
        if (isinstance(invalid_values, range)):
            invalid_values = list(invalid_values)
        self.assertGreater(a=len(values_to_test), b=0)
        self.assert_list_2_contains_all_elements_in_list_1(list_1=valid_values, list_2=values_to_test)
        self.assertLess(a=len(valid_values), b=len(values_to_test))
        self.assertGreater(a=len(valid_values), b=0)
        self.assert_list_2_contains_all_elements_in_list_1(list_1=valid_values, list_2=valid_values_to_save)
        self.assertLess(a=len(valid_values), b=len(valid_values_to_save))
        self.assert_list_2_contains_all_elements_in_list_1(list_1=valid_values_to_save, list_2=values_to_test)
        self.assertLessEqual(a=len(valid_values_to_save), b=len(values_to_test))
        self.assertGreater(a=len(valid_values_to_save), b=0)
        self.assert_list_2_contains_all_elements_in_list_1(list_1=valid_values, list_2=valid_values_to_assign)
        self.assertLess(a=len(valid_values), b=len(valid_values_to_assign))
        self.assert_list_2_contains_all_elements_in_list_1(list_1=valid_values_to_assign, list_2=values_to_test)
        self.assertLessEqual(a=len(valid_values_to_assign), b=len(values_to_test))
        self.assertGreater(a=len(valid_values_to_assign), b=0)
        self.assert_list_2_contains_all_elements_in_list_1(list_1=invalid_values, list_2=values_to_test)
        self.assertLess(a=len(invalid_values), b=len(values_to_test))
        self.assertGreater(a=len(invalid_values), b=0)
        self.assertListEqual(list1=invalid_values, list2=[value for value in values_to_test if (value not in valid_values)])
        self.assertListEqual(list1=valid_values, list2=[value for value in values_to_test if (value not in invalid_values)])
        self.assert_list_2_doesnt_contain_elements_in_list_1(list_1=invalid_values, list_2=valid_values)

    def assert_step_and_error_messages_ok(self, step, error_messages):
        self.assertEqual(first=step, second=len(settings.SPEEDY_MATCH_SITE_PROFILE_FORM_FIELDS))
        self.assertEqual(first=step, second=10)
        self.assertEqual(first=len(error_messages), second=0)
        self.assertListEqual(list1=error_messages, list2=[])

    def save_user_and_profile_and_assert_exceptions_for_integer(self, user, field_name, value_to_test, null):
        if ((null == True) and (value_to_test in self._empty_string_list)):
            with self.assertRaises(ValueError) as cm:
                user.save_user_and_profile()
            self.assertEqual(first=str(cm.exception), second="invalid literal for int() with base 10: ''")
        else:
            with self.assertRaises(ValidationError) as cm:
                user.save_user_and_profile()
            if ((null == False) and (value_to_test in self._none_list)):
                self.assertDictEqual(d1=dict(cm.exception), d2=self._this_field_cannot_be_null_errors_dict_by_field_name(field_name=field_name))
            elif (isinstance(value_to_test, int)):
                self.assertDictEqual(d1=dict(cm.exception), d2=self._value_is_not_a_valid_choice_errors_dict_by_field_name_and_value(field_name=field_name, value=value_to_test))
            else:
                self.assertDictEqual(d1=dict(cm.exception), d2=self._value_must_be_an_integer_errors_dict_by_field_name_and_value(field_name=field_name, value=value_to_test))

    def save_user_and_profile_and_assert_exceptions_for_gender_to_match(self, user, field_name, value_to_test):
        if (isinstance(value_to_test, str)):
            with self.assertRaises(DataError) as cm:
                user.save_user_and_profile()
            # print(str(cm.exception)) # ~~~~ TODO: remove this line!
            self.assertIn(member='malformed array literal: ""', container=str(cm.exception))
        else:
            with self.assertRaises(ValidationError) as cm:
                user.save_user_and_profile()
            # print(str(cm.exception)) # ~~~~ TODO: remove this line!
            # print(dict(cm.exception)) # ~~~~ TODO: remove this line!
            self.assertDictEqual(d1=dict(cm.exception), d2=self._list_contains_items_it_should_contain_no_more_than_3_errors_dict_by_field_name_and_value(field_name=field_name, value=value_to_test))

    def save_user_and_profile_and_assert_exceptions_for_jsonfield(self, user, field_name, value_to_test, blank, null):
        with self.assertRaises(ValidationError) as cm:
            user.save_user_and_profile()
        if ((null == False) and (value_to_test in self._none_list)):
            self.assertDictEqual(d1=dict(cm.exception), d2=self._this_field_cannot_be_null_errors_dict_by_field_name(field_name=field_name))
        elif ((blank == False) and (value_to_test in self._empty_string_list + [list(), tuple(), dict()])):
            self.assertDictEqual(d1=dict(cm.exception), d2=self._this_field_cannot_be_blank_errors_dict_by_field_name(field_name=field_name))
        else:
            self.assertDictEqual(d1=dict(cm.exception), d2=self._value_must_be_valid_json_errors_dict_by_field_name(field_name=field_name))

    def save_user_and_profile_and_assert_exceptions_for_integer_list(self, user, field_name_list, value_to_test, null):
        self.assertTrue(expr=(isinstance(field_name_list, (list, tuple))))
        self.assertTrue(expr=(isinstance(value_to_test, (list, tuple))))
        self.assertEqual(first=len(field_name_list), second=len(value_to_test))
        with self.assertRaises(ValidationError) as cm:
            user.save_user_and_profile()
        if ((null == False) and (all(value_to_test[i] in self._none_list for i in range(len(value_to_test))))):
            self.assertDictEqual(d1=dict(cm.exception), d2=self._this_field_cannot_be_null_errors_dict_by_field_name_list(field_name_list=field_name_list))
        else:
            self.assertDictEqual(d1=dict(cm.exception), d2=self._value_must_be_an_integer_errors_dict_by_field_name_list_and_value_list(field_name_list=field_name_list, value_list=value_to_test))

    def run_test_validate_profile_and_activate_exception(self, test_settings):
        user = ActiveUserFactory()
        # print(test_settings.keys()) # ~~~~ TODO: remove this line!
        # print(set(test_settings.keys())) # ~~~~ TODO: remove this line!
        self.assertIn(member="field_name", container=test_settings.keys())
        field_name = test_settings["field_name"]
        expected_test_settings_keys = {"field_name", "test_invalid_values_to_assign", "test_invalid_values_to_save", "expected_step", "expected_counts_tuple"}
        if (field_name in ['min_max_age_to_match']):
            expected_test_settings_keys.update({"test_invalid_ages", "expected_error_message_min_age_match_and_max_age_match_valid", "expected_error_message_min_age_match_invalid", "expected_error_message_max_age_match_invalid", "expected_error_messages_min_age_match_and_max_age_match_valid", "expected_error_messages_min_age_match_and_max_age_match_invalid", "expected_min_max_age_to_match_error_messages_counts_tuple"})
        elif (field_name in ['diet_match', 'smoking_status_match', 'marital_status_match']):
            expected_test_settings_keys.update({"test_invalid_keys", "test_invalid_ranks", "expected_error_message_keys_and_ranks_invalid", "expected_error_messages_keys_and_ranks_invalid", "expected_error_message_max_rank_invalid", "expected_error_messages_max_rank_invalid", "expected_keys_and_ranks_error_messages_counts_tuple"})
        else:
            expected_test_settings_keys.update({"expected_error_message", "expected_error_messages"})
        self.assertSetEqual(set1=set(test_settings.keys()), set2=expected_test_settings_keys)
        ok_count, validate_profile_and_activate_failures_count, model_assign_failures_count, model_save_failures_count = 0, 0, 0, 0
        error_message_min_age_match_and_max_age_match_valid_count, error_message_min_age_match_and_max_age_match_invalid_count = 0, 0
        error_message_keys_and_ranks_invalid_count, error_message_max_rank_invalid_count = 0, 0
        can_assign_value_set, can_save_user_and_profile_set, value_is_valid_set, value_is_invalid_set = set(), set(), set(), set()
        values_to_test, valid_values_to_assign, valid_values_to_save, valid_values, invalid_values, invalid_values_with_valid_ranks = None, None, None, None, None, None
        if (field_name in ['photo']):
            valid_values = [UserImageFactory]
            values_to_test = self._empty_values_to_test + self._non_int_string_values_to_test + list(range(-10, 10 + 1)) + valid_values
            valid_values_to_assign = self._none_list + valid_values
            valid_values_to_save = valid_values_to_assign
        elif (field_name in ['profile_description', 'city', 'children', 'more_children', 'match_description']):
            values_to_test = self._empty_values_to_test + self._valid_string_values_to_test
            valid_values_to_save = values_to_test
            invalid_values = self._empty_values_to_test
            valid_values = self._valid_string_values_to_test
        elif (field_name in ['height']):
            values_to_test = self._empty_values_to_test + self._non_int_string_values_to_test + list(range(-10, settings.MAX_HEIGHT_ALLOWED + 10 + 1))
            valid_values_to_save = self._none_list + [value for value in values_to_test if (isinstance(value, int))]
            valid_values = SpeedyMatchSiteProfile.HEIGHT_VALID_VALUES
        elif (field_name in ['diet']):
            values_to_test = self._empty_values_to_test + self._non_int_string_values_to_test + list(range(-10, User.DIET_MAX_VALUE_PLUS_ONE + 10))
            valid_values_to_save = [choice[0] for choice in User.DIET_CHOICES_WITH_DEFAULT]
            valid_values = User.DIET_VALID_VALUES
            self.assertEqual(first=valid_values_to_save, second=[User.DIET_UNKNOWN] + valid_values)
            self.assertEqual(first=valid_values_to_save, second=[0] + valid_values)
        elif (field_name in ['smoking_status']):
            values_to_test = self._empty_values_to_test + self._non_int_string_values_to_test + list(range(-10, SpeedyMatchSiteProfile.SMOKING_STATUS_MAX_VALUE_PLUS_ONE + 10))
            valid_values_to_save = [choice[0] for choice in SpeedyMatchSiteProfile.SMOKING_STATUS_CHOICES_WITH_DEFAULT]
            valid_values = SpeedyMatchSiteProfile.SMOKING_STATUS_VALID_VALUES
            self.assertEqual(first=valid_values_to_save, second=[SpeedyMatchSiteProfile.SMOKING_STATUS_UNKNOWN] + valid_values)
            self.assertEqual(first=valid_values_to_save, second=[0] + valid_values)
        elif (field_name in ['marital_status']):
            values_to_test = self._empty_values_to_test + self._non_int_string_values_to_test + list(range(-10, SpeedyMatchSiteProfile.MARITAL_STATUS_MAX_VALUE_PLUS_ONE + 10))
            valid_values_to_save = [choice[0] for choice in SpeedyMatchSiteProfile.MARITAL_STATUS_CHOICES_WITH_DEFAULT]
            valid_values = SpeedyMatchSiteProfile.MARITAL_STATUS_VALID_VALUES
            self.assertEqual(first=valid_values_to_save, second=[SpeedyMatchSiteProfile.MARITAL_STATUS_UNKNOWN] + valid_values)
            self.assertEqual(first=valid_values_to_save, second=[0] + valid_values)
        elif (field_name in ['gender_to_match']):
            range_to_test = [User.GENDER_UNKNOWN] + User.GENDER_VALID_VALUES + [User.GENDER_MAX_VALUE_PLUS_ONE]
            self.assertListEqual(list1=range_to_test, list2=list(range(User.GENDER_UNKNOWN, User.GENDER_MAX_VALUE_PLUS_ONE + 1)))
            self.assertListEqual(list1=range_to_test, list2=list(range(5)))
            self.assertSetEqual(set1=set(range_to_test) - set(User.GENDER_VALID_VALUES), set2={User.GENDER_UNKNOWN, User.GENDER_MAX_VALUE_PLUS_ONE})
            self.assertSetEqual(set1=set(range_to_test) - set(User.GENDER_VALID_VALUES), set2={0, 4})
            self.assert_list_2_contains_all_elements_in_list_1(list_1=User.GENDER_VALID_VALUES, list_2=range_to_test)
            values_to_test = self._empty_values_to_test + [list(), tuple(), User.GENDER_VALID_VALUES + User.GENDER_VALID_VALUES, tuple(User.GENDER_VALID_VALUES + User.GENDER_VALID_VALUES), User.GENDER_VALID_VALUES[0:2] + User.GENDER_VALID_VALUES[0:1], User.GENDER_VALID_VALUES[0:2] + User.GENDER_VALID_VALUES[0:2]]
            for n in range(10 + 1):
                if (n <= len(User.GENDER_VALID_VALUES)):
                    product = list(itertools.product(*itertools.repeat(range_to_test, n)))
                    values_to_test.extend([list(item) for item in product])
                    if (n <= 1):
                        values_to_test.extend(product)
                    else:
                        product = list(itertools.product(*itertools.repeat(User.GENDER_VALID_VALUES, n)))
                        if (n == 2):
                            values_to_test.extend(product[:5])
                        elif (n == 3):
                            values_to_test.extend(product[3:8])
                else:
                    values_to_test.extend([([i] + [item for j in range(10) for item in User.GENDER_VALID_VALUES])[:n] for i in range_to_test])
            valid_values_to_save = self._none_list + [gender_to_match for gender_to_match in values_to_test if ((isinstance(gender_to_match, (list, tuple))) and (len(gender_to_match) <= len(User.GENDER_VALID_VALUES)))]
            valid_values = [gender_to_match for gender_to_match in values_to_test if ((isinstance(gender_to_match, (list, tuple))) and (len(gender_to_match) > 0) and (len(gender_to_match) == len(set(gender_to_match))) and (all(gender in User.GENDER_VALID_VALUES for gender in gender_to_match)))]
            for value in [[1], [2], [3], (1,), (2,), (3,), [1, 2], [1, 3], [2, 3], (1, 2), (1, 3), [1, 2, 3], (1, 2, 3)]:
                for val in [value, list(value)]:
                    self.assertIn(member=val, container=values_to_test)
                    self.assertIn(member=val, container=valid_values)
            for value in [[], (), [1, 2, 3, 1, 2, 3], (1, 2, 3, 1, 2, 3), [1, 2, 1], [1, 2, 1, 2], [0], [4], (0,), (4,), [0, 1], [1, 2, 0], [1, 2, 4], [4, 1, 2, 3]]:
                for val in [value, list(value)]:
                    self.assertIn(member=val, container=values_to_test)
                    self.assertNotIn(member=val, container=valid_values)
                    if (len(val) <= 3):
                        self.assertIn(member=val, container=valid_values_to_save)
                    else:
                        self.assertNotIn(member=val, container=valid_values_to_save)
            for value in valid_values:
                self.assertIn(member=value, container=values_to_test)
            invalid_values = [value for value in values_to_test if (value not in valid_values)]
            for value in invalid_values:
                self.assertIn(member=value, container=values_to_test)
                self.assertNotIn(member=value, container=valid_values)
            for value in [[i, i] for i in User.GENDER_VALID_VALUES] + [[i, i, i] for i in User.GENDER_VALID_VALUES] + [[i, i, 1] for i in User.GENDER_VALID_VALUES]:
                self.assertIn(member=value, container=values_to_test)
                self.assertIn(member=value, container=invalid_values)
            valid_sets = list()
            for value in [set(gender_to_match) for gender_to_match in valid_values]:
                if (value not in valid_sets):
                    valid_sets.append(value)
            # print(valid_sets) # ~~~~ TODO: remove this line!
            self.assertListEqual(list1=valid_sets, list2=[{1}, {2}, {3}, {1, 2}, {1, 3}, {2, 3}, {1, 2, 3}])
        elif (field_name in ['min_age_match', 'max_age_match']):
            values_to_test = self._empty_values_to_test + self._non_int_string_values_to_test + list(range(-10, settings.MAX_AGE_ALLOWED + 10 + 1))
            valid_values_to_save = [value for value in values_to_test if (isinstance(value, int))]
            valid_values = SpeedyMatchSiteProfile.AGE_VALID_VALUES
        elif (field_name in ['min_max_age_to_match']):
            values_to_test_valid_ages = [(value, settings.MAX_AGE_ALLOWED - value) for value in SpeedyMatchSiteProfile.AGE_VALID_VALUES]
            self.assertTrue(expr=all((len(value) == 2) for value in values_to_test_valid_ages))
            values_to_test = []
            if (test_settings["test_invalid_values_to_save"]):
                values_to_test.extend([(value, value) for value in self._empty_values_to_test + self._non_int_string_values_to_test])
            if (test_settings["test_invalid_ages"]):
                values_to_test.extend([(value, settings.MAX_AGE_ALLOWED - value) for value in range(-10, settings.MAX_AGE_ALLOWED + 10 + 1)])
                self.assert_list_2_contains_all_elements_in_list_1(list_1=values_to_test_valid_ages, list_2=values_to_test)
            else:
                values_to_test.extend(values_to_test_valid_ages)
            self.assertTrue(expr=all((len(value) == 2) for value in values_to_test))
            if (test_settings["test_invalid_values_to_save"]):
                valid_values_to_save = [value for value in values_to_test if (all(isinstance(value[i], int) for i in range(len(value))))]
                valid_values = [value for value in values_to_test_valid_ages if (value[0] <= value[1])]
            else:
                valid_values_to_save = values_to_test
                valid_values = [value for value in values_to_test if (value[0] <= value[1])]
            invalid_values = [value for value in values_to_test if (value not in valid_values)]
            self.assertListEqual(list1=valid_values, list2=[(value, 180 - value) for value in range(0, 90 + 1)])
            self.assertEqual(first=valid_values[0], second=(0, 180))
            self.assertEqual(first=valid_values[-1], second=(90, 90))
            if (test_settings["test_invalid_ages"]):
                invalid_values_valid_ages = [value for value in values_to_test_valid_ages if (value not in valid_values)]
                self.assert_list_2_contains_all_elements_in_list_1(list_1=invalid_values_valid_ages, list_2=invalid_values)
                self.assertListEqual(list1=invalid_values_valid_ages, list2=[(value, 180 - value) for value in range(91, 180 + 1)])
                self.assertEqual(first=invalid_values_valid_ages[0], second=(91, 89))
                self.assertEqual(first=invalid_values_valid_ages[-1], second=(180, 0))
                self.assertListEqual(list1=invalid_values, list2=[(value, value) for value in self._empty_values_to_test + self._non_int_string_values_to_test] + [(value, 180 - value) for value in (list(range(-10, 0)) + list(range(91, 180 + 10 + 1)))])
                self.assertEqual(first=invalid_values[0], second=(None, None))
                self.assertEqual(first=invalid_values[-1], second=(190, -10))
                self.assertListEqual(list1=invalid_values[16:-10], list2=invalid_values_valid_ages)
                self.assertListEqual(list1=invalid_values[16:106], list2=invalid_values_valid_ages)
            else:
                self.assertListEqual(list1=invalid_values, list2=[(value, 180 - value) for value in range(91, 180 + 1)])
                self.assertEqual(first=invalid_values[0], second=(91, 89))
                self.assertEqual(first=invalid_values[-1], second=(180, 0))
        elif (field_name in ['diet_match', 'smoking_status_match', 'marital_status_match']):
            if (field_name in ['diet_match']):
                all_keys = User.DIET_VALID_VALUES
            elif (field_name in ['smoking_status_match']):
                all_keys = SpeedyMatchSiteProfile.SMOKING_STATUS_VALID_VALUES
            elif (field_name in ['marital_status_match']):
                all_keys = SpeedyMatchSiteProfile.MARITAL_STATUS_VALID_VALUES
            else:
                raise Exception("Unexpected: field_name={}".format(field_name))
            all_keys_with_invalid_keys = ["___"] + [all_keys[0] - 1] + all_keys + [all_keys[-1] + 1]
            if (test_settings["test_invalid_ranks"]):
                range_to_test = [SpeedyMatchSiteProfile.RANK_VALID_VALUES[0] - 1] + SpeedyMatchSiteProfile.RANK_VALID_VALUES + [SpeedyMatchSiteProfile.RANK_VALID_VALUES[-1] + 1]
                expected_range_to_test_list = list(range(-1, 6 + 1))
                expected_invalid_keys_set = {-1, 6}
            else:
                range_to_test = SpeedyMatchSiteProfile.RANK_VALID_VALUES
                expected_range_to_test_list = list(range(0, 5 + 1))
                expected_invalid_keys_set = set()
            self.assertListEqual(list1=range_to_test, list2=expected_range_to_test_list)
            self.assertSetEqual(set1=set(range_to_test) - set(SpeedyMatchSiteProfile.RANK_VALID_VALUES), set2=expected_invalid_keys_set)
            self.assert_list_2_contains_all_elements_in_list_1(list_1=SpeedyMatchSiteProfile.RANK_VALID_VALUES, list_2=range_to_test)
            values_to_test, valid_values_to_save, valid_values, invalid_values_with_valid_ranks = [], [], [], []
            if (test_settings["test_invalid_values_to_save"]):
                values_to_test.extend(self._empty_values_to_test + [list(), tuple(), dict(), set()])
            if (test_settings["test_invalid_keys"]):
                for key in all_keys_with_invalid_keys:
                    value_to_test = self.get_field_default_value(field_name=field_name)
                    if (key in all_keys):
                        del value_to_test[str(key)]
                    else:
                        value_to_test[str(key)] = SpeedyMatchSiteProfile.RANK_5
                    valid_values_to_save.append(value_to_test)
            for item in itertools.product(*itertools.repeat(range_to_test, 2)):
                self.assertEqual(first=len(item), second=2)
                # If both values are equal, it's enough to add value_to_test once.
                if (item[0] == item[1]):
                    key_range = all_keys[0:1]
                else:
                    key_range = all_keys
                for key in key_range:
                    value_to_test = self.get_field_default_value(field_name=field_name)
                    for value_to_test_key in all_keys:
                        if (value_to_test_key == key):
                            i = 0
                        else:
                            i = 1
                        value_to_test[str(value_to_test_key)] = item[i]
                    valid_values_to_save.append(value_to_test)
                    all_ranks_are_valid = all(value in SpeedyMatchSiteProfile.RANK_VALID_VALUES for value in item)
                    max_rank_is_valid = (max(item) == 5)
                    self.assertEqual(first=all_ranks_are_valid, second=all(validators.rank_is_valid(rank=value) for value in item))
                    self.assertEqual(first=max_rank_is_valid, second=(max(item) == SpeedyMatchSiteProfile.RANK_5))
                    # print(item, value_to_test, max(item), all_ranks_are_valid, max_rank_is_valid) # ~~~~ TODO: remove this line!
                    if (all_ranks_are_valid):
                        if (max_rank_is_valid):
                            valid_values.append(value_to_test)
                        else:
                            invalid_values_with_valid_ranks.append(value_to_test)
            values_to_test.extend(valid_values_to_save)
        if (valid_values_to_assign is None):
            valid_values_to_assign = values_to_test
        if (invalid_values is None):
            invalid_values = [value for value in values_to_test if (value not in valid_values)]
        # print(len(values_to_test)) # ~~~~ TODO: remove this line!
        # print(values_to_test) # ~~~~ TODO: remove this line!
        # print(len(valid_values_to_save)) # ~~~~ TODO: remove this line!
        # print(valid_values_to_save) # ~~~~ TODO: remove this line!
        # print(len(valid_values)) # ~~~~ TODO: remove this line!
        # print(valid_values) # ~~~~ TODO: remove this line!
        self.assert_valid_values_ok(values_to_test=values_to_test, valid_values_to_assign=valid_values_to_assign, valid_values_to_save=valid_values_to_save, valid_values=valid_values, invalid_values=invalid_values)
        if (field_name in ['photo']):
            self.assertTrue(expr=test_settings["test_invalid_values_to_assign"])
        else:
            self.assertFalse(expr=test_settings["test_invalid_values_to_assign"])
        if (test_settings["test_invalid_values_to_assign"]):
            self.assertLess(a=len(valid_values_to_assign), b=len(values_to_test))
        else:
            self.assertEqual(first=len(valid_values_to_assign), second=len(values_to_test))
            self.assertListEqual(list1=valid_values_to_assign, list2=values_to_test)
        if (test_settings["test_invalid_values_to_save"]):
            self.assertLess(a=len(valid_values_to_save), b=len(valid_values_to_assign))
        else:
            self.assertEqual(first=len(valid_values_to_save), second=len(valid_values_to_assign))
            self.assertListEqual(list1=valid_values_to_save, list2=valid_values_to_assign)
        if (field_name in ['diet_match', 'smoking_status_match', 'marital_status_match']):
            self.assertGreater(a=len(invalid_values_with_valid_ranks), b=0)
            self.assert_list_2_contains_all_elements_in_list_1(list_1=invalid_values_with_valid_ranks, list_2=invalid_values)
        else:
            self.assertIsNone(obj=invalid_values_with_valid_ranks)
        for value_to_test in values_to_test:
            can_assign_value = (value_to_test in valid_values_to_assign)
            can_save_user_and_profile = (value_to_test in valid_values_to_save)
            value_is_valid = (value_to_test in valid_values)
            value_is_invalid = (value_to_test in invalid_values)
            self.assertEqual(first=value_is_valid, second=(not (value_is_invalid)))
            can_assign_value_set.add(can_assign_value)
            # print(value_to_test) # ~~~~ TODO: remove this line!
            if (field_name in ['photo']):
                user.photo = None
                if (value_to_test == UserImageFactory):
                    value_to_assign = UserImageFactory(owner=user)
                else:
                    value_to_assign = value_to_test
            else:
                value_to_assign = value_to_test
            if (not (can_assign_value)):
                if (field_name in ['photo']):
                    with self.assertRaises(ValueError) as cm:
                        user.photo = value_to_assign
                    self.assertEqual(first=str(cm.exception), second='Cannot assign "{0}{1}{0}": "User.photo" must be a "Image" instance.'.format("'" if (isinstance(value_to_assign, str)) else '', value_to_assign))
                    user.save_user_and_profile()
                    self.assertEqual(first=user.photo, second=None)
                    self.assertNotEqual(first=user.photo, second=value_to_assign)
                else:
                    raise Exception("Unexpected: can_assign_value={}, value_to_test={}".format(can_assign_value, value_to_test))
                model_assign_failures_count += 1
            else:
                if (field_name in ['photo']):
                    user.photo = value_to_assign
                elif (field_name in ['profile_description']):
                    user.profile.profile_description = value_to_assign
                elif (field_name in ['city']):
                    user.profile.city = value_to_assign
                elif (field_name in ['children']):
                    user.profile.children = value_to_assign
                elif (field_name in ['more_children']):
                    user.profile.more_children = value_to_assign
                elif (field_name in ['match_description']):
                    user.profile.match_description = value_to_assign
                elif (field_name in ['height']):
                    user.profile.height = value_to_assign
                elif (field_name in ['diet']):
                    user.diet = value_to_assign
                elif (field_name in ['smoking_status']):
                    user.profile.smoking_status = value_to_assign
                elif (field_name in ['marital_status']):
                    user.profile.marital_status = value_to_assign
                elif (field_name in ['gender_to_match']):
                    user.profile.gender_to_match = value_to_assign
                elif (field_name in ['min_age_match']):
                    user.profile.min_age_match = value_to_assign
                elif (field_name in ['max_age_match']):
                    user.profile.max_age_match = value_to_assign
                elif (field_name in ['min_max_age_to_match']):
                    user.profile.min_age_match = value_to_assign[0]
                    user.profile.max_age_match = value_to_assign[1]
                elif (field_name in ['diet_match']):
                    user.profile.diet_match = value_to_assign
                elif (field_name in ['smoking_status_match']):
                    user.profile.smoking_status_match = value_to_assign
                elif (field_name in ['marital_status_match']):
                    user.profile.marital_status_match = value_to_assign
                can_save_user_and_profile_set.add(can_save_user_and_profile)
                if (not (can_save_user_and_profile)):
                    if (field_name in ['height']):
                        self.save_user_and_profile_and_assert_exceptions_for_integer(user=user, field_name=field_name, value_to_test=value_to_test, null=True)
                    elif (field_name in ['diet', 'smoking_status', 'marital_status', 'min_age_match', 'max_age_match']):
                        self.save_user_and_profile_and_assert_exceptions_for_integer(user=user, field_name=field_name, value_to_test=value_to_test, null=False)
                    elif (field_name in ['min_max_age_to_match']):
                        self.save_user_and_profile_and_assert_exceptions_for_integer_list(user=user, field_name_list=['min_age_match', 'max_age_match'], value_to_test=value_to_test, null=False)
                    elif (field_name in ['gender_to_match']):
                        self.save_user_and_profile_and_assert_exceptions_for_gender_to_match(user=user, field_name=field_name, value_to_test=value_to_test)
                    elif (field_name in ['diet_match', 'smoking_status_match', 'marital_status_match']):
                        self.save_user_and_profile_and_assert_exceptions_for_jsonfield(user=user, field_name=field_name, value_to_test=value_to_test, blank=False, null=False)
                    else:
                        raise Exception("Unexpected: can_save_user_and_profile={}, value_to_test={}".format(can_save_user_and_profile, value_to_test))
                    model_save_failures_count += 1
                else:
                    value_is_valid_set.add(value_is_valid)
                    value_is_invalid_set.add(value_is_invalid)
                    user.save_user_and_profile()
                    step, error_messages = user.profile.validate_profile_and_activate()
                    if (not (value_is_valid)):
                        self.assertEqual(first=step, second=test_settings["expected_step"])
                        # print(error_messages) # ~~~~ TODO: remove this line!
                        if (field_name in ['min_max_age_to_match']):
                            self.assertTrue(expr=(isinstance(value_to_test, (list, tuple))))
                            if (all(value_to_test[i] in SpeedyMatchSiteProfile.AGE_VALID_VALUES for i in range(2))):
                                expected_error_messages_len = 1
                                expected_error_messages_key = "expected_error_messages_min_age_match_and_max_age_match_valid"
                                fields_and_error_messages = [(field_name, "expected_error_message_min_age_match_and_max_age_match_valid")]
                                error_message_min_age_match_and_max_age_match_valid_count += 1
                            else:
                                self.assertTrue(expr=test_settings["test_invalid_ages"])
                                expected_error_messages_len = 2
                                expected_error_messages_key = "expected_error_messages_min_age_match_and_max_age_match_invalid"
                                fields_and_error_messages = []
                                for _field_name in ['min_age_match', 'max_age_match', 'min_max_age_to_match']:
                                    if (_field_name in ['min_max_age_to_match']):
                                        fields_and_error_messages.append((_field_name, None))
                                    else:
                                        fields_and_error_messages.append((_field_name, "expected_error_message_{}_invalid".format(_field_name)))
                                error_message_min_age_match_and_max_age_match_invalid_count += 1
                        elif (field_name in ['diet_match', 'smoking_status_match', 'marital_status_match']):
                            if (not (value_to_test in invalid_values_with_valid_ranks)):
                                expected_error_messages_len = 1
                                expected_error_messages_key = "expected_error_messages_keys_and_ranks_invalid"
                                fields_and_error_messages = [(field_name, "expected_error_message_keys_and_ranks_invalid")]
                                error_message_keys_and_ranks_invalid_count += 1
                            else:
                                expected_error_messages_len = 1
                                expected_error_messages_key = "expected_error_messages_max_rank_invalid"
                                fields_and_error_messages = [(field_name, "expected_error_message_max_rank_invalid")]
                                error_message_max_rank_invalid_count += 1
                        else:
                            expected_error_messages_len = 1
                            expected_error_messages_key = "expected_error_messages"
                            fields_and_error_messages = [(field_name, "expected_error_message")]
                        self.assertEqual(first=len(error_messages), second=expected_error_messages_len)
                        self.assertListEqual(list1=error_messages, list2=test_settings[expected_error_messages_key])
                        for (_field_name, expected_error_message_key) in fields_and_error_messages:
                            if (expected_error_message_key is None):
                                utils.validate_field(field_name=_field_name, user=user)
                            else:
                                with self.assertRaises(ValidationError) as cm:
                                    utils.validate_field(field_name=_field_name, user=user)
                                self.assertEqual(first=str(cm.exception.message), second=test_settings[expected_error_message_key])
                                self.assertListEqual(list1=list(cm.exception), list2=[test_settings[expected_error_message_key]])
                        validate_profile_and_activate_failures_count += 1
                    else:
                        self.assert_step_and_error_messages_ok(step=step, error_messages=error_messages)
                        utils.validate_field(field_name=field_name, user=user)
                        ok_count += 1
        if (test_settings["test_invalid_values_to_assign"]):
            self.assertSetEqual(set1=can_assign_value_set, set2={False, True})
        else:
            self.assertSetEqual(set1=can_assign_value_set, set2={True})
        if (test_settings["test_invalid_values_to_save"]):
            self.assertSetEqual(set1=can_save_user_and_profile_set, set2={False, True})
        else:
            self.assertSetEqual(set1=can_save_user_and_profile_set, set2={True})
        self.assertSetEqual(set1=value_is_valid_set, set2={False, True})
        self.assertSetEqual(set1=value_is_invalid_set, set2={False, True})
        self.assertGreater(a=ok_count, b=0)
        self.assertGreater(a=validate_profile_and_activate_failures_count, b=0)
        if (test_settings["test_invalid_values_to_assign"]):
            self.assertGreater(a=model_assign_failures_count, b=0)
        else:
            self.assertEqual(first=model_assign_failures_count, second=0)
        if (test_settings["test_invalid_values_to_save"]):
            self.assertGreater(a=model_save_failures_count, b=0)
        else:
            self.assertEqual(first=model_save_failures_count, second=0)
        counts_tuple = (ok_count, validate_profile_and_activate_failures_count, model_assign_failures_count, model_save_failures_count)
        min_max_age_to_match_error_messages_counts_tuple = (error_message_min_age_match_and_max_age_match_valid_count, error_message_min_age_match_and_max_age_match_invalid_count)
        keys_and_ranks_error_messages_counts_tuple = (error_message_keys_and_ranks_invalid_count, error_message_max_rank_invalid_count)
        self.assertEqual(first=sum(counts_tuple), second=len(values_to_test))
        self.assertTupleEqual(tuple1=counts_tuple, tuple2=(len(valid_values), len(valid_values_to_save) - len(valid_values), len(values_to_test) - len(valid_values_to_assign), len(valid_values_to_assign) - len(valid_values_to_save)))
        self.assertTupleEqual(tuple1=counts_tuple, tuple2=test_settings["expected_counts_tuple"])
        if (field_name in ['min_max_age_to_match']):
            self.assertEqual(first=sum(min_max_age_to_match_error_messages_counts_tuple), second=validate_profile_and_activate_failures_count)
            self.assertTupleEqual(tuple1=min_max_age_to_match_error_messages_counts_tuple, tuple2=test_settings["expected_min_max_age_to_match_error_messages_counts_tuple"])
        else:
            self.assertEqual(first=sum(min_max_age_to_match_error_messages_counts_tuple), second=0)
            self.assertTupleEqual(tuple1=min_max_age_to_match_error_messages_counts_tuple, tuple2=(0, 0))
        if (field_name in ['diet_match', 'smoking_status_match', 'marital_status_match']):
            self.assertEqual(first=sum(keys_and_ranks_error_messages_counts_tuple), second=validate_profile_and_activate_failures_count)
            self.assertTupleEqual(tuple1=keys_and_ranks_error_messages_counts_tuple, tuple2=test_settings["expected_keys_and_ranks_error_messages_counts_tuple"])
        else:
            self.assertEqual(first=sum(keys_and_ranks_error_messages_counts_tuple), second=0)
            self.assertTupleEqual(tuple1=keys_and_ranks_error_messages_counts_tuple, tuple2=(0, 0))

    def test_height_valid_values(self):
        self.assertEqual(first=settings.MIN_HEIGHT_ALLOWED, second=1)
        self.assertEqual(first=settings.MAX_HEIGHT_ALLOWED, second=450)
        self.assertEqual(first=SpeedyMatchSiteProfile.HEIGHT_VALID_VALUES, second=range(settings.MIN_HEIGHT_ALLOWED, settings.MAX_HEIGHT_ALLOWED + 1))
        self.assertEqual(first=SpeedyMatchSiteProfile.HEIGHT_VALID_VALUES, second=range(1, 450 + 1))

    def test_age_valid_values(self):
        self.assertEqual(first=settings.MIN_AGE_ALLOWED, second=0)
        self.assertEqual(first=settings.MAX_AGE_ALLOWED, second=180)
        self.assertEqual(first=SpeedyMatchSiteProfile.AGE_VALID_VALUES, second=range(settings.MIN_AGE_ALLOWED, settings.MAX_AGE_ALLOWED + 1))
        self.assertEqual(first=SpeedyMatchSiteProfile.AGE_VALID_VALUES, second=range(0, 180 + 1))

    def test_smoking_status_valid_values(self):
        self.assertListEqual(list1=SpeedyMatchSiteProfile.SMOKING_STATUS_VALID_VALUES, list2=list(range(SpeedyMatchSiteProfile.SMOKING_STATUS_UNKNOWN + 1, SpeedyMatchSiteProfile.SMOKING_STATUS_MAX_VALUE_PLUS_ONE)))
        self.assertListEqual(list1=SpeedyMatchSiteProfile.SMOKING_STATUS_VALID_VALUES, list2=list(range(1, 3 + 1)))

    def test_marital_status_valid_values(self):
        self.assertListEqual(list1=SpeedyMatchSiteProfile.MARITAL_STATUS_VALID_VALUES, list2=list(range(SpeedyMatchSiteProfile.MARITAL_STATUS_UNKNOWN + 1, SpeedyMatchSiteProfile.MARITAL_STATUS_MAX_VALUE_PLUS_ONE)))
        self.assertListEqual(list1=SpeedyMatchSiteProfile.MARITAL_STATUS_VALID_VALUES, list2=list(range(1, 8 + 1)))

    def test_rank_valid_values(self):
        self.assertListEqual(list1=SpeedyMatchSiteProfile.RANK_VALID_VALUES, list2=list(range(SpeedyMatchSiteProfile.RANK_0, SpeedyMatchSiteProfile.RANK_5 + 1)))
        self.assertListEqual(list1=SpeedyMatchSiteProfile.RANK_VALID_VALUES, list2=list(range(0, 5 + 1)))

    def test_diet_match_default(self):
        diet_match = SpeedyMatchSiteProfile.diet_match_default()
        self.assertSetEqual(set1=set(diet_match.keys()), set2={str(diet) for diet in User.DIET_VALID_VALUES})
        self.assertSetEqual(set1={diet_match[key] for key in diet_match}, set2={SpeedyMatchSiteProfile.RANK_5})
        self.assertSetEqual(set1={diet_match[str(diet)] for diet in User.DIET_VALID_VALUES}, set2={SpeedyMatchSiteProfile.RANK_5})
        self.assertListEqual(list1=[diet_match[str(diet)] for diet in User.DIET_VALID_VALUES], list2=[5 for diet in User.DIET_VALID_VALUES])

    def test_smoking_status_match_default(self):
        smoking_status_match = SpeedyMatchSiteProfile.smoking_status_match_default()
        self.assertSetEqual(set1=set(smoking_status_match.keys()), set2={str(smoking_status) for smoking_status in SpeedyMatchSiteProfile.SMOKING_STATUS_VALID_VALUES})
        self.assertSetEqual(set1={smoking_status_match[key] for key in smoking_status_match}, set2={SpeedyMatchSiteProfile.RANK_5})
        self.assertSetEqual(set1={smoking_status_match[str(smoking_status)] for smoking_status in SpeedyMatchSiteProfile.SMOKING_STATUS_VALID_VALUES}, set2={SpeedyMatchSiteProfile.RANK_5})
        self.assertListEqual(list1=[smoking_status_match[str(smoking_status)] for smoking_status in SpeedyMatchSiteProfile.SMOKING_STATUS_VALID_VALUES], list2=[5 for smoking_status in SpeedyMatchSiteProfile.SMOKING_STATUS_VALID_VALUES])

    def test_marital_status_match_default(self):
        marital_status_match = SpeedyMatchSiteProfile.marital_status_match_default()
        self.assertSetEqual(set1=set(marital_status_match.keys()), set2={str(marital_status) for marital_status in SpeedyMatchSiteProfile.MARITAL_STATUS_VALID_VALUES})
        self.assertSetEqual(set1={marital_status_match[key] for key in marital_status_match}, set2={SpeedyMatchSiteProfile.RANK_5})
        self.assertSetEqual(set1={marital_status_match[str(marital_status)] for marital_status in SpeedyMatchSiteProfile.MARITAL_STATUS_VALID_VALUES}, set2={SpeedyMatchSiteProfile.RANK_5})
        self.assertListEqual(list1=[marital_status_match[str(marital_status)] for marital_status in SpeedyMatchSiteProfile.MARITAL_STATUS_VALID_VALUES], list2=[5 for marital_status in SpeedyMatchSiteProfile.MARITAL_STATUS_VALID_VALUES])

    def test_get_steps_range(self):
        self.assertEqual(first=len(settings.SPEEDY_MATCH_SITE_PROFILE_FORM_FIELDS), second=10)
        self.assertEqual(first=utils.get_steps_range(), second=range(1, len(settings.SPEEDY_MATCH_SITE_PROFILE_FORM_FIELDS)))
        self.assertEqual(first=utils.get_steps_range(), second=range(1, 10))

    def test_get_active_languages(self):
        p = SpeedyMatchSiteProfile(active_languages='en, he, de')
        self.assertListEqual(list1=p.get_active_languages(), list2=['en', 'he', 'de'])
        p = SpeedyMatchSiteProfile(active_languages='')
        self.assertListEqual(list1=p.get_active_languages(), list2=[])

    def test_set_active_languages(self):
        p = SpeedyMatchSiteProfile()
        p._set_active_languages(['en', 'he'])
        self.assertSetEqual(set1=set(p.get_active_languages()), set2={'en', 'he'})

    def test_call_activate_directly_and_assert_exception(self):
        user = self.get_default_user_1()
        self.assertEqual(first=user.is_active, second=True)
        self.assertEqual(first=user.profile.is_active, second=False)
        with self.assertRaises(NotImplementedError) as cm:
            user.profile.activate()
        self.assertEqual(first=str(cm.exception), second="activate is not implemented.")
        self.assertEqual(first=user.is_active, second=True)
        self.assertEqual(first=user.profile.is_active, second=False)

    def test_call_deactivate_directly_and_assert_no_exception(self):
        user = self.get_default_user_2()
        self.assertEqual(first=user.is_active, second=True)
        self.assertEqual(first=user.profile.is_active, second=True)
        user.profile.deactivate()
        self.assertEqual(first=user.is_active, second=True)
        self.assertEqual(first=user.profile.is_active, second=False)

    def test_call_get_name_directly_and_assert_no_exception(self):
        user = self.get_default_user_1()
        self.assertEqual(first=user.profile.get_name(), second='Jesse')

    def test_call_str_of_user_directly_and_assert_no_exception(self):
        user = self.get_default_user_1()
        self.assertEqual(first=str(user), second='Jesse')

    def test_validate_profile_and_activate_ok(self):
        user = ActiveUserFactory()
        step, error_messages = user.profile.validate_profile_and_activate()
        self.assert_step_and_error_messages_ok(step=step, error_messages=error_messages)
        self.assertIn(member=user.gender, container=User.GENDER_VALID_VALUES)
        self.assertIn(member=user.diet, container=User.DIET_VALID_VALUES)
        self.assertIn(member=user.profile.height, container=SpeedyMatchSiteProfile.HEIGHT_VALID_VALUES)
        self.assertIn(member=user.profile.smoking_status, container=SpeedyMatchSiteProfile.SMOKING_STATUS_VALID_VALUES)
        self.assertIn(member=user.profile.marital_status, container=SpeedyMatchSiteProfile.MARITAL_STATUS_VALID_VALUES)
        self.assertIn(member=user.profile.min_age_match, container=SpeedyMatchSiteProfile.AGE_VALID_VALUES)
        self.assertIn(member=user.profile.max_age_match, container=SpeedyMatchSiteProfile.AGE_VALID_VALUES)
        self.assertEqual(first=user.profile.min_age_match, second=settings.MIN_AGE_ALLOWED)
        self.assertEqual(first=user.profile.max_age_match, second=settings.MAX_AGE_ALLOWED)
        self.validate_all_user_values(user=user)

    def test_validate_profile_and_activate_exception_on_photo(self):
        test_settings = {
            "field_name": 'photo',
            "test_invalid_values_to_assign": True,
            "test_invalid_values_to_save": False,
            "expected_step": 2,
            "expected_error_message": 'A profile picture is required.',
            "expected_error_messages": ["['A profile picture is required.']"],
            "expected_counts_tuple": (1, 1, 26, 0),
        }
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_profile_description(self):
        test_settings = {
            "field_name": 'profile_description',
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": False,
            "expected_step": 3,
            "expected_error_message": 'Please write some text in this field.',
            "expected_error_messages": ["['Please write some text in this field.']"],
            "expected_counts_tuple": (5, 2, 0, 0),
        }
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_city(self):
        test_settings = {
            "field_name": 'city',
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": False,
            "expected_step": 3,
            "expected_error_message": 'Please write where you live.',
            "expected_error_messages": ["['Please write where you live.']"],
            "expected_counts_tuple": (5, 2, 0, 0),
        }
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_children(self):
        test_settings = {
            "field_name": 'children',
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": False,
            "expected_step": 4,
            "expected_error_message": 'Do you have children? How many?',
            "expected_error_messages": ["['Do you have children? How many?']"],
            "expected_counts_tuple": (5, 2, 0, 0),
        }
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_more_children(self):
        test_settings = {
            "field_name": 'more_children',
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": False,
            "expected_step": 4,
            "expected_error_message": 'Do you want (more) children?',
            "expected_error_messages": ["['Do you want (more) children?']"],
            "expected_counts_tuple": (5, 2, 0, 0),
        }
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_match_description(self):
        test_settings = {
            "field_name": 'match_description',
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": False,
            "expected_step": 7,
            "expected_error_message": 'Please write some text in this field.',
            "expected_error_messages": ["['Please write some text in this field.']"],
            "expected_counts_tuple": (5, 2, 0, 0),
        }
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_height(self):
        test_settings = {
            "field_name": 'height',
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": True,
            "expected_step": 3,
            "expected_error_message": 'Height must be from 1 to 450 cm.',
            "expected_error_messages": ["['Height must be from 1 to 450 cm.']"],
            "expected_counts_tuple": (450, 22, 0, 5),
        }
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_diet(self):
        test_settings = {
            "field_name": 'diet',
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": True,
            "expected_step": 5,
            "expected_error_message": 'Your diet is required.',
            "expected_error_messages": ["['Your diet is required.']"],
            "expected_counts_tuple": (3, 1, 0, 26),
        }
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_smoking_status(self):
        test_settings = {
            "field_name": 'smoking_status',
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": True,
            "expected_step": 5,
            "expected_error_message": 'Your smoking status is required.',
            "expected_error_messages": ["['Your smoking status is required.']"],
            "expected_counts_tuple": (3, 1, 0, 26),
        }
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_marital_status(self):
        test_settings = {
            "field_name": 'marital_status',
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": True,
            "expected_step": 6,
            "expected_error_message": 'Your marital status is required.',
            "expected_error_messages": ["['Your marital status is required.']"],
            "expected_counts_tuple": (8, 1, 0, 26),
        }
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_gender_to_match(self):
        test_settings = {
            "field_name": 'gender_to_match',
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": True,
            "expected_step": 7,
            "expected_error_message": 'Gender to match is required.',
            "expected_error_messages": ["['Gender to match is required.']"],
            "expected_counts_tuple": (23, 153, 0, 39),
        }
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_min_age_match(self):
        test_settings = {
            "field_name": 'min_age_match',
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": True,
            "expected_step": 7,
            "expected_error_message": 'Minimal age to match must be from 0 to 180 years.',
            "expected_error_messages": ["['Minimal age to match must be from 0 to 180 years.']"],
            "expected_counts_tuple": (181, 20, 0, 6),
        }
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_max_age_match(self):
        test_settings = {
            "field_name": 'max_age_match',
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": True,
            "expected_step": 7,
            "expected_error_message": 'Maximal age to match must be from 0 to 180 years.',
            "expected_error_messages": ["['Maximal age to match must be from 0 to 180 years.']"],
            "expected_counts_tuple": (181, 20, 0, 6),
        }
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_min_max_age_to_match_without_invalid_ages_and_invalid_values_to_save(self):
        test_settings = self.get_min_max_age_to_match_default_test_settings()
        test_settings.update({
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": False,
            "test_invalid_ages": False,
            "expected_counts_tuple": (91, 90, 0, 0),
            "expected_min_max_age_to_match_error_messages_counts_tuple": (90, 0),
        })
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_min_max_age_to_match_with_invalid_ages_and_invalid_values_to_save(self):
        test_settings = self.get_min_max_age_to_match_default_test_settings()
        test_settings.update({
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": True,
            "test_invalid_ages": True,
            "expected_counts_tuple": (91, 110, 0, 6),
            "expected_min_max_age_to_match_error_messages_counts_tuple": (90, 20),
        })
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_diet_match_with_invalid_keys_and_ranks_and_invalid_values_to_save(self):
        test_settings = self.get_diet_match_default_test_settings()
        test_settings.update({
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": True,
            "test_invalid_keys": True,
            "test_invalid_ranks": True,
            "expected_counts_tuple": (31, 151, 0, 6),
            "expected_keys_and_ranks_error_messages_counts_tuple": (86, 65),
        })
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_diet_match_without_invalid_keys_and_ranks_and_invalid_values_to_save(self):
        test_settings = self.get_diet_match_default_test_settings()
        test_settings.update({
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": False,
            "test_invalid_keys": False,
            "test_invalid_ranks": False,
            "expected_counts_tuple": (31, 65, 0, 0),
            "expected_keys_and_ranks_error_messages_counts_tuple": (0, 65),
        })
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_smoking_status_match_with_invalid_keys_and_ranks_and_invalid_values_to_save(self):
        test_settings = self.get_smoking_status_match_default_test_settings()
        test_settings.update({
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": True,
            "test_invalid_keys": True,
            "test_invalid_ranks": True,
            "expected_counts_tuple": (31, 151, 0, 6),
            "expected_keys_and_ranks_error_messages_counts_tuple": (86, 65),
        })
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_smoking_status_match_without_invalid_keys_and_ranks_and_invalid_values_to_save(self):
        test_settings = self.get_smoking_status_match_default_test_settings()
        test_settings.update({
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": False,
            "test_invalid_keys": False,
            "test_invalid_ranks": False,
            "expected_counts_tuple": (31, 65, 0, 0),
            "expected_keys_and_ranks_error_messages_counts_tuple": (0, 65),
        })
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_marital_status_match_with_invalid_keys_and_ranks_and_invalid_values_to_save(self):
        test_settings = self.get_marital_status_match_default_test_settings()
        test_settings.update({
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": True,
            "test_invalid_keys": True,
            "test_invalid_ranks": True,
            "expected_counts_tuple": (81, 386, 0, 6),
            "expected_keys_and_ranks_error_messages_counts_tuple": (221, 165),
        })
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)

    def test_validate_profile_and_activate_exception_on_marital_status_match_without_invalid_keys_and_ranks_and_invalid_values_to_save(self):
        test_settings = self.get_marital_status_match_default_test_settings()
        test_settings.update({
            "test_invalid_values_to_assign": False,
            "test_invalid_values_to_save": False,
            "test_invalid_keys": False,
            "test_invalid_ranks": False,
            "expected_counts_tuple": (81, 165, 0, 0),
            "expected_keys_and_ranks_error_messages_counts_tuple": (0, 165),
        })
        self.run_test_validate_profile_and_activate_exception(test_settings=test_settings)


@only_on_speedy_match
class SpeedyMatchSiteProfileMatchTestCase(TestCase):
    def get_default_user_1(self):
        user = ActiveUserFactory(first_name='Walter', last_name='White', slug='walter', date_of_birth=date(year=1958, month=10, day=22), gender=User.GENDER_MALE)
        user.diet = User.DIET_VEGETARIAN
        user.profile.smoking_status = SpeedyMatchSiteProfile.SMOKING_STATUS_NO
        user.profile.marital_status = SpeedyMatchSiteProfile.MARITAL_STATUS_SINGLE
        user.profile.min_age_match = 20
        user.profile.max_age_match = 180
        user.profile.gender_to_match = [User.GENDER_FEMALE]
        user.save_user_and_profile()
        return user

    def get_default_user_2(self):
        user = ActiveUserFactory(first_name='Jesse', last_name='Pinkman', slug='jesse-pinkman', date_of_birth=date(year=1978, month=9, day=12), gender=User.GENDER_FEMALE)
        user.diet = User.DIET_VEGAN
        user.profile.smoking_status = SpeedyMatchSiteProfile.SMOKING_STATUS_YES
        user.profile.marital_status = SpeedyMatchSiteProfile.MARITAL_STATUS_SINGLE
        user.profile.gender_to_match = [User.GENDER_MALE]
        user.save_user_and_profile()
        return user

    def test_user_doesnt_match_self(self):
        user = ActiveUserFactory()
        for gender in User.GENDER_VALID_VALUES:
            user.gender = gender
            user.profile.gender_to_match = User.GENDER_VALID_VALUES
            user.save_user_and_profile()
            rank = user.profile.get_matching_rank(other_profile=user.profile)
            self.assertEqual(first=rank, second=0)

    def test_gender_doesnt_match_profile(self):
        user_1 = self.get_default_user_1()
        user_2 = self.get_default_user_2()
        user_1.profile.gender_to_match = [User.GENDER_MALE]
        user_2.profile.gender_to_match = [User.GENDER_MALE]
        user_1.save_user_and_profile()
        user_2.save_user_and_profile()
        rank_1 = user_1.profile.get_matching_rank(other_profile=user_2.profile)
        self.assertEqual(first=rank_1, second=0)
        rank_2 = user_2.profile.get_matching_rank(other_profile=user_1.profile)
        self.assertEqual(first=rank_2, second=0)

    def test_gender_match_profile_different_gender(self):
        user_1 = self.get_default_user_1()
        user_2 = self.get_default_user_2()
        user_1.save_user_and_profile()
        user_2.save_user_and_profile()
        rank_1 = user_1.profile.get_matching_rank(other_profile=user_2.profile)
        self.assertEqual(first=rank_1, second=5)
        rank_2 = user_2.profile.get_matching_rank(other_profile=user_1.profile)
        self.assertEqual(first=rank_2, second=5)

    def test_gender_match_profile_same_gender(self):
        user_1 = self.get_default_user_1()
        user_2 = self.get_default_user_2()
        user_1.profile.gender_to_match = [User.GENDER_MALE]
        user_2.gender = User.GENDER_MALE
        user_2.profile.gender_to_match = [User.GENDER_MALE]
        user_1.save_user_and_profile()
        user_2.save_user_and_profile()
        rank_1 = user_1.profile.get_matching_rank(other_profile=user_2.profile)
        self.assertEqual(first=rank_1, second=5)
        rank_2 = user_2.profile.get_matching_rank(other_profile=user_1.profile)
        self.assertEqual(first=rank_2, second=5)

    def test_age_doesnt_match_profile(self):
        user_1 = self.get_default_user_1()
        user_2 = self.get_default_user_2()
        user_1.profile.min_age_match = 20
        user_1.profile.max_age_match = 30
        user_1.save_user_and_profile()
        user_2.save_user_and_profile()
        rank_1 = user_1.profile.get_matching_rank(other_profile=user_2.profile)
        self.assertEqual(first=rank_1, second=0)
        rank_2 = user_2.profile.get_matching_rank(other_profile=user_1.profile)
        self.assertEqual(first=rank_2, second=0)

    def test_smoking_status_doesnt_match_profile(self):
        user_1 = self.get_default_user_1()
        user_2 = self.get_default_user_2()
        user_1.profile.smoking_status_match = {str(SpeedyMatchSiteProfile.SMOKING_STATUS_YES): 0, str(SpeedyMatchSiteProfile.SMOKING_STATUS_NO): 5, str(SpeedyMatchSiteProfile.SMOKING_STATUS_SOMETIMES): 0}
        user_2.profile.smoking_status = SpeedyMatchSiteProfile.SMOKING_STATUS_YES
        user_1.save_user_and_profile()
        user_2.save_user_and_profile()
        rank_1 = user_1.profile.get_matching_rank(other_profile=user_2.profile)
        self.assertEqual(first=rank_1, second=0)
        rank_2 = user_2.profile.get_matching_rank(other_profile=user_1.profile)
        self.assertEqual(first=rank_2, second=0)

    def test_marital_status_match_profile(self):
        user_1 = self.get_default_user_1()
        user_2 = self.get_default_user_2()
        user_2.profile.marital_status_match[str(SpeedyMatchSiteProfile.MARITAL_STATUS_MARRIED)] = SpeedyMatchSiteProfile.RANK_0
        user_1.save_user_and_profile()
        user_2.save_user_and_profile()
        rank_1 = user_1.profile.get_matching_rank(other_profile=user_2.profile)
        self.assertEqual(first=rank_1, second=5)
        rank_2 = user_2.profile.get_matching_rank(other_profile=user_1.profile)
        self.assertEqual(first=rank_2, second=5)

    def test_marital_status_doesnt_match_profile(self):
        user_1 = self.get_default_user_1()
        user_2 = self.get_default_user_2()
        user_1.profile.marital_status = SpeedyMatchSiteProfile.MARITAL_STATUS_MARRIED
        user_2.profile.marital_status_match[str(SpeedyMatchSiteProfile.MARITAL_STATUS_MARRIED)] = SpeedyMatchSiteProfile.RANK_0
        user_1.save_user_and_profile()
        user_2.save_user_and_profile()
        rank_1 = user_1.profile.get_matching_rank(other_profile=user_2.profile)
        self.assertEqual(first=rank_1, second=0)
        rank_2 = user_2.profile.get_matching_rank(other_profile=user_1.profile)
        self.assertEqual(first=rank_2, second=0)

    def test_match_profile_rank_3(self):
        user_1 = self.get_default_user_1()
        user_2 = self.get_default_user_2()
        user_1.profile.smoking_status_match = {str(SpeedyMatchSiteProfile.SMOKING_STATUS_YES): 3, str(SpeedyMatchSiteProfile.SMOKING_STATUS_NO): 5, str(SpeedyMatchSiteProfile.SMOKING_STATUS_SOMETIMES): 4}
        user_1.profile.diet_match = {str(User.DIET_VEGAN): 4, str(User.DIET_VEGETARIAN): 5, str(User.DIET_CARNIST): 0}
        user_1.save_user_and_profile()
        user_2.save_user_and_profile()
        rank_1 = user_1.profile.get_matching_rank(other_profile=user_2.profile)
        self.assertEqual(first=rank_1, second=3)
        rank_2 = user_2.profile.get_matching_rank(other_profile=user_1.profile)
        self.assertEqual(first=rank_2, second=5)

    def test_match_profile_rank_4(self):
        user_1 = self.get_default_user_1()
        user_2 = self.get_default_user_2()
        user_1.profile.diet_match = {str(User.DIET_VEGAN): 4, str(User.DIET_VEGETARIAN): 5, str(User.DIET_CARNIST): 0}
        user_1.save_user_and_profile()
        user_2.save_user_and_profile()
        rank_1 = user_1.profile.get_matching_rank(other_profile=user_2.profile)
        self.assertEqual(first=rank_1, second=4)
        rank_2 = user_2.profile.get_matching_rank(other_profile=user_1.profile)
        self.assertEqual(first=rank_2, second=5)

    def test_match_profile_rank_1(self):
        user_1 = self.get_default_user_2()
        user_2 = self.get_default_user_1()
        user_1.profile.smoking_status_match = {str(SpeedyMatchSiteProfile.SMOKING_STATUS_YES): 3, str(SpeedyMatchSiteProfile.SMOKING_STATUS_NO): 5, str(SpeedyMatchSiteProfile.SMOKING_STATUS_SOMETIMES): 4}
        user_1.profile.diet_match = {str(User.DIET_VEGAN): 4, str(User.DIET_VEGETARIAN): 5, str(User.DIET_CARNIST): 0}
        user_1.profile.marital_status_match[str(SpeedyMatchSiteProfile.MARITAL_STATUS_MARRIED)] = SpeedyMatchSiteProfile.RANK_1
        user_2.profile.marital_status = SpeedyMatchSiteProfile.MARITAL_STATUS_MARRIED
        user_1.save_user_and_profile()
        user_2.save_user_and_profile()
        rank_1 = user_1.profile.get_matching_rank(other_profile=user_2.profile)
        self.assertEqual(first=rank_1, second=1)
        rank_2 = user_2.profile.get_matching_rank(other_profile=user_1.profile)
        self.assertEqual(first=rank_2, second=5)


