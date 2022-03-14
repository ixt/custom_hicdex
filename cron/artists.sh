#!/bin/bash

BASE=/home/biker/hicdex/hicdex
cd ${BASE} && docker-compose run --rm idx ruby /myapp/artist.rb $*
