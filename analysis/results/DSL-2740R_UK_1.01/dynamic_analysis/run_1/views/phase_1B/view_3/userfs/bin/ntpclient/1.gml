graph [
  directed 1
  node [
    id 0
    label "socket(domain:2, type:1, protocol:17){addr:127.0.0.1; port:53}"
    kind "channel"
  ]
  node [
    id 1
    label "<border>"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/userfs/bin/ntpclient"
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
]
