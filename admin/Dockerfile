# Specify the image that will be used to create the container.
# You can choose the most suitable one for you: https://hub.docker.com/_/python
FROM python:3.12
# Choose the folder where project files will be located inside the container.
# Keep in mind that the WORKDIR command will create the /opt/app folder if it doesn't exis
# and switch to that folder, meaning all commands after WORKDIR will be executed in
# the /opt/app folder
WORKDIR /opt/app
# Set the necessary environment variables
ENV DJANGO_SETTINGS_MODULE 'config.settings'
# Copy files that rarely change into the container.
# We recommend using the run_uwsgi.sh script as the entry point to the application.
# There you can perform necessary procedures before starting the application,
# such as collecting static files, creating a superuser, and even applying migrations
COPY requirements.txt requirements.txt
# Install dependencies, having first updated the pip package manager
RUN pip install --upgrade pip \
    && pip install -r requirements.txt
# Copy all remaining files. To speed up image building, this command should be placed clos
# The dot in the COPY command means the current folder.
# So we're asking docker to copy all files from the current folder to the current folder i
COPY . .
RUN chmod +x entrypoint.sh
# Specify the port on which the application will be available inside the Docker network
EXPOSE 8000
# Specify how to start your service.
# The ENTRYPOINT instruction specifies the entry point to the application.
# For simplicity, we immediately launch uwsgi, but you might find it more convenient
# to specify the run_uwsgi.sh file here, and launch the application within it
ENTRYPOINT ["./entrypoint.sh"]