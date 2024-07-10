import os
from dotenv import load_dotenv
from sqlalchemy import Column, Integer, String, ForeignKey, Table, BLOB, create_engine
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

load_dotenv()
Base = declarative_base()


class Organisation(Base):
    __tablename__ = "organisations"
    org_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    org_type = Column(String)
    parent_org_id = Column(String, ForeignKey("organisations.org_id"))
    link = Column(String)
    homepage = Column(String)
    org_id_tumonline = Column(Integer)
    hierarchy = Column(Integer)

    parent_org = relationship("Organisation", remote_side=[org_id])
    children_orgs = relationship("Organisation", back_populates="parent_org")


class Module(Base):
    __tablename__ = "modules"
    module_id = Column(Integer, primary_key=True)
    module_id_uni = Column(String)
    name = Column(String)
    org_id = Column(String, ForeignKey("organisations.org_id"))
    level = Column(String)
    lang = Column(String)
    ects = Column(Integer)
    prereq = Column(String)
    description = Column(String)
    valid_from = Column(String)
    valid_to = Column(String)
    link = Column(String)
    link_type = Column(String)
    digital_score = Column(Integer)

    organisation = relationship("Organisation")
    topics = relationship("ModuleTopicMapping", back_populates="module")

    def __str__(self):
        return f"Module(id={self.module_id}, name='{self.name}', lang='{self.lang}', level='{self.level}', org_id={self.org_id})"
        # Customize the output format based on your Module class attributes

        # Optional: Define __repr__ for formal representation

    def __repr__(self):
        return f"<Module(id={self.org_id}, name='{self.name}')>"


class Topic(Base):
    __tablename__ = "topics"
    topic_id = Column(Integer, primary_key=True)
    topic = Column(String, nullable=False)
    embedding = Column(BLOB)

    modules = relationship("ModuleTopicMapping", back_populates="topic")

    def __repr__(self):
        return f"<Topic(id={self.topic_id}, topic='{self.topic}')>"


class ModuleTopicMapping(Base):
    __tablename__ = "module_topic_mappings"
    module_id = Column(Integer, ForeignKey("modules.module_id"), primary_key=True)
    topic_id = Column(Integer, ForeignKey("topics.topic_id"), primary_key=True)

    module = relationship("Module", back_populates="topics")
    topic = relationship("Topic", back_populates="modules")


# Connect to the existing database
engine = create_engine(f'sqlite:///{os.getenv("DB_PATH")}')

# Create a configured "Session" class
Session = sessionmaker(bind=engine)
