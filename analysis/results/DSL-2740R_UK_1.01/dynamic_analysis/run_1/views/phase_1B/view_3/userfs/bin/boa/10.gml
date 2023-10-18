graph [
  directed 1
  node [
    id 0
    label "socket(domain:10, type:2, protocol:6){addr:0.65.139.180; port:80}"
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
    label "/userfs/bin/boa"
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
