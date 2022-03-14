#!/usr/bin/env ruby

require 'fileutils'
require 'open3'

BACKUP_PATH = "/mnt/data/backups/daily"
REORG_FILE = "/home/biker/hicdex/infos/reorg.txt"
RESTORE_SCRIPT = "/home/biker/hicdex/hicdex/cron/restore.sh"
MINUTES_AGO = 10

test = ARGV[0] == 'test'
last_reorg = nil
if File.exists?(REORG_FILE)
  content = File.read(REORG_FILE)
  data = content.split("\n").detect { |e| e != '' }.split("#")
  last_reorg = data[0].strip
elsif !test
  exit
else
  last_reorg = Time.at(Time.now().to_i - 120).strftime('%Y%m%d-%H%M%S')
end

puts "Reorg found @ #{last_reorg}"

# find the most recent backup just before the reorg
# backup have to be older than X minutes to be sure that there was enough time to complete
min_backup_time = Time.at(Time.now().to_i - MINUTES_AGO * 60)

min_backup = "dipdup-#{min_backup_time.strftime('%Y%m%d-%H%M%S')}"
min_reorg = "dipdup-#{last_reorg}"
list = Dir.glob("#{BACKUP_PATH}/*.sql.gz").sort { |a,b| b<=>a }
use_backup = nil
list.each do |f|
  name = f.split('/').last
  ok = (name<=min_backup) && (name<=min_reorg)
  puts "#{name} - #{min_reorg} = #{ok ? 'OK' : 'KO'}"
  next unless ok
  use_backup = f
  break
end

if !use_backup then
  puts "ERROR: unable to find a proper backup !"
  exit(255)
end

puts "Restoring backup #{use_backup}"
exit if test

Open3.popen2e(RESTORE_SCRIPT, use_backup) do |input, output, t|
  output.each { |line| puts line }
end
