graph [
  directed 1
  node [
    id 0
    label "socket(domain:16, type:3, protocol:0){pid:0; groups:1024}"
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
    label "/userfs/bin/dnsmasq"
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
