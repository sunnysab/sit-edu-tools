from typing import List
from enum import Enum
from collections import namedtuple

# TODO: 增加教学班ID、名称、课程代码等字段
__elements = [
    ('course_name', '课程名称', 'kcmc'),
    ('day', '星期', 'xqjmc'),
    ('time_index', '节次', 'jcs'),
    ('weeks', '周次', 'zcd'),
    ('place', '教室', 'cdmc'),
    ('teacher', '教师', 'xm'),
    ('campus', '校区', 'xqmc'),
]

# New namedtuple type
Course = namedtuple('Course', [x for x, _, _ in __elements])


# An enum of semester
class Semester(Enum):
    FIRST_TERM = 1
    SECOND_TERM = 2

    def to_raw(self) -> int:
        if self == self.FIRST_TERM:
            return 3
        elif self == self.SECOND_TERM:
            return 12


# Day map
DAY_MAP = {
    '星期一': 1,
    '星期二': 2,
    '星期三': 3,
    '星期四': 4,
    '星期五': 5,
    '星期六': 6,
    '星期日': 7,
}


def get_timetable_url(user: str) -> str:
    return f'http://jwxt.sit.edu.cn/jwglxt/kbcx/xskbcx_cxXsKb.html?gnmkdm=N253508&su=#{user}'


def __expand_weeks_str(week_string: str) -> tuple:
    """
    Expand weeks' str to a tuple of weeks.
    For example: We gets a string '1-6周(单)', so the function returns a tuple of (1, 3, 5)
    Last but not least, multi-section-string like '1-9周,11-12周,14周' is supported.
    :return: A tuple that indicates the weeks.
    """
    if ',' in week_string:  # Call self recursively
        weeks = []
        for x in week_string.split(','):
            weeks.extend(__expand_weeks_str(x))
    else:
        step = 2 if week_string.endswith('(单)') or week_string.endswith('(双)') else 1
        try:
            start, end = week_string[:week_string.index('周')].split('-')
            weeks = list(range(int(start), int(end) + 1, step))
        except ValueError:
            # ValueError is going to be thrown when week_string may be like '3周'
            weeks = week_string[:week_string.index('周')]
            weeks = [int(weeks)]

    return tuple(weeks)


def __expand_time_index(time_string: str) -> tuple:
    """
    Expand time string like '1-2' to a tuple of indices.
    :return: a tuple of indices
    """
    try:
        start, end = time_string.split('-')
        indices = list(range(int(start), int(end) + 1))
    except ValueError:
        # ValueError is going to be thrown when week_string may be like '1'
        indices = [int(time_string)]
    return tuple(indices)


# TODO: 合并同类课程
def parse_timetable_page(page: str) -> List[Course]:
    json_page = json.loads(page)
    course_list = json_page['kbList']
    result = []

    for course in course_list:
        fields = {}

        for field_name, _, raw_name in __elements:
            fields[field_name] = course[raw_name]

        """
            Some more processes
        """
        # '1-3周,5周' -> (1, 2, 3, 5)
        fields['weeks'] = __expand_weeks_str(fields['weeks'])
        # '1-3' -> (1, 2, 3)
        fields['time_index'] = __expand_time_index(fields['time_index'])
        # '赵,钱,孙,李' -> ['赵','钱','孙','李']
        fields['teacher'] = fields['teacher'].split(',')
        # '星期一' -> 1
        fields['day'] = DAY_MAP[fields['day']]

        result.append(Course(**fields))

    return result


if __name__ == '__main__':
    import json

    content = json.load(open('timetable.json', 'r', encoding='utf-8'))
    print(parse_timetable_page(content))
