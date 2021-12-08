# TODO: remove this file when batch is called directly by cloudtask and remaining enqueued tasks have been leased

import logging

from pydantic import BaseModel

from pcapi import settings
from pcapi.notifications.push import delete_user_attributes
from pcapi.notifications.push import update_user_attributes
from pcapi.notifications.push.backends.batch import BatchAPI
from pcapi.tasks.decorator import task


logger = logging.getLogger(__name__)


class UpdateBatchAttributesRequest(BaseModel):
    attributes: dict
    user_id: int


class DeleteBatchUserAttributesRequest(BaseModel):
    user_id: int


@task(settings.GCP_BATCH_CUSTOM_DATA_ANDROID_QUEUE_NAME, "/batch/android/update_user_attributes")
def update_user_attributes_android_task(payload: UpdateBatchAttributesRequest) -> None:
    update_user_attributes(BatchAPI.ANDROID, payload.user_id, payload.attributes)


@task(settings.GCP_BATCH_CUSTOM_DATA_IOS_QUEUE_NAME, "/batch/ios/update_user_attributes")
def update_user_attributes_ios_task(payload: UpdateBatchAttributesRequest) -> None:
    update_user_attributes(BatchAPI.IOS, payload.user_id, payload.attributes)


@task(settings.GCP_BATCH_CUSTOM_DATA_QUEUE_NAME, "/batch/delete_user_attributes")
def delete_user_attributes_task(payload: DeleteBatchUserAttributesRequest) -> None:
    delete_user_attributes(payload.user_id)
