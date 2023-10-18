graph [
  directed 1
  node [
    id 0
    label "socket(domain:10, type:3, protocol:58){addr:0.0.0.0; port:0}"
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
    label "/userfs/bin/radvd"
    kind "executable"
    listening 1
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
