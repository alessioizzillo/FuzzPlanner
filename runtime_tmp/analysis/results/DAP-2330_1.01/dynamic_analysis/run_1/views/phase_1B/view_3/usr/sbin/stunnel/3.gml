graph [
  directed 1
  node [
    id 0
    label "socket(domain:1, type:1, protocol:0){path:/dev/log}"
    kind "channel"
  ]
  node [
    id 1
    label "/sbin/httpd"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/sbin/syslogd"
    kind "executable"
    listening 0
  ]
  node [
    id 3
    label "/usr/sbin/stunnel"
    kind "executable"
    listening 0
  ]
  node [
    id 4
    label "/usr/sbin/login"
    kind "executable"
    listening 0
  ]
  edge [
    source 0
    target 2
  ]
  edge [
    source 1
    target 0
  ]
  edge [
    source 3
    target 0
  ]
  edge [
    source 4
    target 0
  ]
]
