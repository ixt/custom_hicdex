# syntax=docker/dockerfile:1
FROM ruby:2.7.5
RUN apt-get update -qq && apt-get install -y nodejs postgresql-client

WORKDIR /myapp
COPY Gemfile /myapp/Gemfile
# COPY Gemfile.lock /myapp/Gemfile.lock
RUN bundle install

WORKDIR /myapp
COPY . .

# Configure the main process to run when running the image
CMD ["ruby", "/myapp/process_block.rb", "all"]