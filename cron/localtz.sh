#!/usr/bin/env node
// replace all UTC dates to local dates in pipe
// usage: docker logs -t container_name | docker-logs-localtime

// install:	
// curl https://gist.githubusercontent.com/popstas/ffcf282492fd78389d1df2ab7f31052a/raw/505cdf97c6a1edbb10c3b2b64e1836e0627b87a0/docker-logs-localtime > /usr/local/bin/docker-logs-localtime && chmod +x /usr/local/bin/docker-logs-localtime	

// alternative: https://github.com/HuangYingNing/docker-logs-localtime

const pad = d => (d > 9 ? d : '0' + d);

Date.prototype.outDateTime = function() {
  return (
    [this.getFullYear(), pad(this.getMonth() + 1), pad(this.getDate())].join('-') +
    ' ' +
    [pad(this.getHours()), pad(this.getMinutes()), pad(this.getSeconds())].join(':')
  );
};

process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', function(data) {
  data = data.replace(/\.\d+Z /g, ' ');
  const match = data.match(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/g);
  if (match) {
    match.forEach(dateUtc => {
      const d = new Date(dateUtc);
      const offset = new Date().getTimezoneOffset() * 60000;
      const dateLocal = new Date(d.getTime() - offset).outDateTime();
      data = data.replace(dateUtc, dateLocal);
    });
  }
  process.stdout.write(data);
});
