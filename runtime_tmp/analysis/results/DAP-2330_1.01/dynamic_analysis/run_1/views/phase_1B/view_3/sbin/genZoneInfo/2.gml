graph [
  directed 1
  node [
    id 0
    label "file{path:/var/zoneinfo}"
    kind "channel"
  ]
  node [
    id 1
    label "/sbin/genZoneInfo"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/sbin/zic"
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
