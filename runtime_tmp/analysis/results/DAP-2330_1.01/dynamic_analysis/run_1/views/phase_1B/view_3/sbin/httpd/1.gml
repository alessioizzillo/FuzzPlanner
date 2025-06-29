graph [
  directed 1
  node [
    id 0
    label "virtual_file{path:/var/proc/web/session:1/user/ac_auth}"
    kind "channel"
  ]
  node [
    id 1
    label "/usr/sbin/xmldb"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/sbin/httpd"
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
