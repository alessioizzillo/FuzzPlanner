graph [
  directed 1
  node [
    id 0
    label "file{path:/var/log/messages}"
    kind "channel"
  ]
  node [
    id 1
    label "/sbin/syslogd"
    kind "executable"
    listening 0
  ]
  edge [
    source 0
    target 1
  ]
  edge [
    source 1
    target 0
  ]
]
