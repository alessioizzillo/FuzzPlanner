graph [
  directed 1
  multigraph 1
  node [
    id 0
    label "/usr/sbin/servd"
    start_time "1688562168959"
    score 0.0
    is_proprietary 1
  ]
  node [
    id 1
    label "/usr/sbin/service"
    start_time "1688562179457"
    score 0.0
    is_proprietary 1
  ]
  edge [
    source 0
    target 1
    key 0
    edge_name "socket(domain:1, type:2, protocol:0){path:/var/run/servd_ctrl_usock}"
    score 0.0
    time "1688562179478"
  ]
  edge [
    source 1
    target 0
    key 0
    edge_name "socket(domain:1, type:2, protocol:0){path:/var/run/servd_ctrl_usock}"
    score 0.0
    time "1688562179471"
  ]
]
