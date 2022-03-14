# About

This is a custom tailored version of hicdex, built to run nftbiker.xyz tools.
The best way to start is try to run the official hicdex, as you can probably find more help on this subject.
Once you succeded to do it, then you can move to this version as it's the same with additionnal code

First you must copy .env.template to .env, and define each parameters in it

Then it use docker to run everything

```
docker-compose up -d
```

If you are on a macbook m1

```
./mac.sh up -d
```

Dig into the docker file to see what services run, and adapt path to your environment.


# Views

Tools use some views that are defined in queries/my_view.sql file.
Must be manually added once the database have been created by hicdex.

# Crontab

A few external scripts run to maintain consistency of database or get some external data (like wallet profiles infos)

```
* * * * * /home/biker/hicdex/hicdex/cron/check.sh
*/10 * * * * /home/biker/hicdex/hicdex/cron/auto.rb >> /home/biker/hicdex/logs/restore.log 2>&1
0 * * * * cd /home/biker/hicdex/hicdex && docker-compose run --rm fxhash >> /home/biker/hicdex/logs/fxhash.log 2>&1
30 6,18 * * * /home/biker/hicdex/hicdex/cron/artists.sh >>  /home/biker/hicdex/logs/artist.log 2>&1
50 * * * * /home/biker/hicdex/hicdex/cron/token.sh >>  /home/biker/hicdex/logs/tokens.log 2>&1
```


- check.sh: extract indexer status for tools page to show current statu
- auto.rb : check if there is a rollback and restart the indexer from a backup
- fxhash : old script to ensure that token balance and blacklisted token are properly accounted
- artist.sh: retrieve wallet infos
- token.sh: build some token stats for marketplace stats
