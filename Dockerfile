FROM python:3


# install dependencies
RUN pip install --upgrade pip
COPY requirements.txt Django-service/
RUN pip install -r Django-service/requirements.txt

# copy project
COPY ./social_web Django-service/social_web

WORKDIR Django-service/social_web/