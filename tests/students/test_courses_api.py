import random

import pytest
from model_bakery import baker
from rest_framework.test import APIClient
from students.models import Course, Student


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def data_factory():
    def factory(*args, **kwargs):
        student_set = baker.prepare(Student, _quantity=5)
        return baker.make(Course, *args, students=student_set, **kwargs)
    return factory


@pytest.mark.django_db
def test_api_get(client, data_factory):
    # Arrange
    courses = data_factory(_quantity=3)

    # Act
    response = client.get('/api/v1/courses/1/')

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert courses[0].name == data['name']


@pytest.mark.django_db
def test_api_list_get(client, data_factory):
    # Arrange
    courses = data_factory(_quantity=3)

    # Act
    response = client.get('/api/v1/courses/')

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(courses)
    for i, n in enumerate(data):
        assert n['name'] == courses[i].name


@pytest.mark.django_db
def test_api_filter_id(client, data_factory):
    # Arrange
    courses = data_factory(_quantity=3)
    id_range = random.choice([c_id.id for c_id in courses])

    # Act
    response = client.get(f'/api/v1/courses/?id={id_range}')

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data[0]['id'] == id_range


@pytest.mark.django_db
def test_api_filter_name(client, data_factory):
    # Arrange
    course = data_factory(_quantity=1)

    # Act
    response_bad = client.get('/api/v1/courses/?name=test')
    response_good = client.get(f'/api/v1/courses/?name={course[0].name}')

    # Assert
    assert response_bad.status_code == 200
    assert response_good.status_code == 200

    data_bad = response_bad.json()
    data_good = response_good.json()

    assert course[0].name == data_good[0]['name']  # checking valid data
    try:
        assert course[0].name == data_bad[0]['name']  # checking empty response, still a success
    except IndexError:
        print('Empty result, no such name')


@pytest.mark.django_db
def test_create_course(client):
    create_data = {
        'name': 'course1'
    }
    response_post = client.post('/api/v1/courses/', data=create_data)
    response_get = client.get('/api/v1/courses/')

    assert response_post.status_code == 201
    assert response_get.status_code == 200
    data = response_get.json()
    assert data[0]['name'] == create_data['name']


@pytest.mark.django_db
def test_update_course(client, data_factory):
    course = data_factory(_quantity=1)
    id = course[0].id
    update_data = {
        'name': 'new_course'
    }

    response_patch = client.patch(f'/api/v1/courses/{id}/', data=update_data)
    response_get_after = client.get(f'/api/v1/courses/{id}/')

    assert response_patch.status_code == 200
    after_data = response_get_after.json()
    assert course[0].name != update_data['name']
    assert after_data['name'] == update_data['name']


@pytest.mark.django_db
def test_update_course(client, data_factory):
    course = data_factory(_quantity=1)
    id = course[0].id

    response_get = client.get(f'/api/v1/courses/{id}/')
    response_delete = client.delete(f'/api/v1/courses/{id}/')
    response_get_after = client.get(f'/api/v1/courses/{id}/')

    assert response_get.status_code == 200
    data = response_get.json()
    assert len(data) > 0
    assert response_delete.status_code == 204
    assert response_get_after.status_code == 404


@pytest.mark.parametrize(
    ['max_students', 'students_created'],
    (
        (20, 10),
        pytest.param(20, 30, marks=pytest.mark.xfail),
    )
)
@pytest.mark.django_db
def test_max_students(client, settings, django_assert_max_num_queries, max_students, students_created):
    settings.USE_MAX_STUDENTS_PER_COURSE = max_students
    assert settings.USE_MAX_STUDENTS_PER_COURSE
    with django_assert_max_num_queries(settings.USE_MAX_STUDENTS_PER_COURSE):
        baker.make(Student, _quantity=students_created)
