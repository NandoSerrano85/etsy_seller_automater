from server.src.routes.auth.service import verify_password, get_password_hash
from server.src.entities.user import User
from server.src.message import (
    UserNotFoundError,
    InvalidPasswordError,
    PasswordLengthInvalidError,
    PasswordMismatchError,
    UserChangePasswordError
)
from uuid import UUID
from sqlalchemy.orm import Session
from . import model
import logging


def get_user_by_id(db: Session, user_id: UUID) -> model.UserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logging.warning(f"User not found with ID: {user_id}")
        raise UserNotFoundError(user_id)

    logging.info(f"Successfully retrived user with ID: {user_id}")
    return user

def change_password(db: Session, user_id: UUID, password_change: model.PasswordChangeRequest) -> None:
    try:
        current_user = get_user_by_id(db, user_id)

        if not verify_password(password_change.current_password, current_user.hashed_password):
            logging.warning(f"Invalid current password provided for user ID: {user_id}")
            raise InvalidPasswordError()

        if len(password_change.new_password) < 6:
            logging.warning(f"New password length is less then 6 characters for user ID: {user_id}")
            raise PasswordLengthInvalidError()
        
        if password_change.new_password != password_change.new_password_confirm:
            logging.warning(f"New password and new password confirmation did not match up for user ID: {user_id}")
            raise PasswordMismatchError()

        # Hash new password
        new_hashed_password = get_password_hash(password_change.new_password)
        
        # Update user password
        current_user.hashed_password = new_hashed_password
        db.commit()

        logging.info(f"Successfully updated password for user: {user_id}")
    except Exception as e:
        logging.error(f"Error during password change for user ID: {user_id}. Error: {e}")
        raise UserChangePasswordError()