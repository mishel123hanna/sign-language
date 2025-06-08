# from sqlmodel import SQLModel, Field
# from datetime import datetime
# from typing import Optional

# class User(SQLModel, table=True):
#     """User model for authentication and history tracking"""
#     id: Optional[int] = Field(default=None, primary_key=True)
#     username: str = Field(unique=True, index=True)
#     email: str = Field(unique=True, index=True)
#     hashed_password: str
#     is_active: bool = Field(default=True)
#     created_at: datetime = Field(default_factory=datetime.now)

    # cloud
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime

class SignGesture(SQLModel, table=True):
    """Model for sign language gestures"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    video_path: str  # Path to the reference video for this sign
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    translations: List["SignTranslation"] = Relationship(back_populates="gesture")


class SignTranslation(SQLModel, table=True):
    """Model for translations of signs to text in various languages"""
    id: Optional[int] = Field(default=None, primary_key=True)
    gesture_id: int = Field(foreign_key="signgesture.id")
    language_code: str  # e.g., "ar" for Arabic
    text: str
    
    # Relationships
    gesture: SignGesture = Relationship(back_populates="translations")


class User(SQLModel, table=True):
    """User model for authentication and history tracking"""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    translation_history: List["TranslationHistory"] = Relationship(back_populates="user")


class TranslationHistory(SQLModel, table=True):
    """Model to store user translation history"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    input_type: str  # "sign_to_text" or "text_to_sign"
    input_content: str  # Text input or reference to video file
    output_content: str  # Result text or reference to output video
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="translation_history")