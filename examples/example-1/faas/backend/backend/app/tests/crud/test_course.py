import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import courses
from app.models import Course
from app.schemas.course_schema import CourseUpdate
from app.tests.utils.models import (
    create_random_user,
    random_course_info,
)
from app.tests.utils.utils import check_updated_fields, num_rows_in_tbl


@pytest.mark.anyio
async def test_create_course(db: AsyncSession):
    """Test create course."""
    user_model = await create_random_user(db)

    rows = await num_rows_in_tbl(db, Course)

    course_info = random_course_info(user_model.id)
    db_course = await courses.create(db, obj_in=course_info)

    assert await num_rows_in_tbl(db, Course) == rows + 1
    assert db_course.name == course_info.name
    assert db_course.creator_id == course_info.creator_id


@pytest.mark.anyio
async def test_read_course(db: AsyncSession):
    """Test reading a course."""
    user_model = await create_random_user(db)

    course_info = random_course_info(user_model.id)
    db_course = await courses.create(db, obj_in=course_info)
    read_id_course = await courses.get(db, db_course.id)
    read_name_course = await courses.get_by_name(db, db_course.name)

    assert db_course == read_id_course
    assert db_course == read_name_course


@pytest.mark.anyio
async def test_read_course_none(db: AsyncSession):
    """Test reading a course when no course exists."""
    course_id = 100000000
    course_name = "fake_course_name"
    read_id_course = await courses.get(db, course_id)
    read_name_course = await courses.get_by_name(db, course_name)

    assert read_id_course is None
    assert read_name_course is None


@pytest.mark.anyio
async def test_delete_course(db: AsyncSession):
    """Test delete course."""
    user_model = await create_random_user(db)

    course_info = random_course_info(user_model.id)
    db_course = await courses.create(db, obj_in=course_info)

    rows = await num_rows_in_tbl(db, Course)

    del_course = await courses.delete(db, key=db_course.id)

    assert await num_rows_in_tbl(db, Course) == rows - 1
    assert await courses.get(db, db_course.id) is None
    assert db_course == del_course


@pytest.mark.anyio
async def test_delete_nonexistent_course(db: AsyncSession):
    """Test delete a course that doesn't exist."""
    rows = await num_rows_in_tbl(db, Course)

    del_course = await courses.delete(db, key=1000000)

    assert await num_rows_in_tbl(db, Course) == rows
    assert del_course is None


@pytest.mark.anyio
async def test_update_course(db: AsyncSession):
    """Test update course."""
    user_model = await create_random_user(db)

    course_info = random_course_info(user_model.id)
    db_course = await courses.create(db, obj_in=course_info)
    old_info = jsonable_encoder(db_course)

    update_info = CourseUpdate(name="new_name")

    db_update = await courses.update(db, key=db_course.id, obj_in=update_info)
    new_info = jsonable_encoder(db_update)

    check_updated_fields(Course, old_info, new_info, update_info)


@pytest.mark.anyio
async def test_get_all_course_names(db: AsyncSession):
    """Test getting all course names."""
    rows = await num_rows_in_tbl(db, Course)

    all_course_names = await courses.get_all_course_names(db)
    assert len(all_course_names) == rows

    for c_id, name in all_course_names:
        assert isinstance(c_id, int)
        assert isinstance(name, str)
