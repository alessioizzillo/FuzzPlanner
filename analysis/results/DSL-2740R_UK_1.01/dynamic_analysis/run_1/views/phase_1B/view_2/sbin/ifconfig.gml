graph [
  directed 1
  multigraph 1
  node [
    id 0
    label "/sbin/ifconfig"
    start_time "1688561599444"
    score 0.8
    is_proprietary 0
  ]
  node [
    id 1
    label "/usr/script/wan_stop.sh"
    start_time "1688561712483"
    score 0.65
    is_proprietary 1
  ]
  node [
    id 2
    label "/bin/sh"
    start_time "1688561600077"
    score 2.1999999999999993
    is_proprietary 0
  ]
  node [
    id 3
    label "/usr/script/ether_mac.sh"
    start_time "1688561605313"
    score 0.65
    is_proprietary 1
  ]
  node [
    id 4
    label "/usr/etc/init.d/rcS"
    start_time "1688561599441"
    score 0.5
    is_proprietary 0
  ]
  node [
    id 5
    label "/usr/script/wan_start.sh"
    start_time "1688561602423"
    score 4.65
    is_proprietary 1
  ]
  node [
    id 6
    label "/bin/sed"
    start_time "1688561599448"
    score 0.0
    is_proprietary 0
  ]
  edge [
    source 0
    target 4
    key 0
    edge_name "pipe_50_4_5"
    score 0.0
    time "1688561599559"
  ]
  edge [
    source 0
    target 5
    key 0
    edge_name "file{path:/etc/mac.conf}"
    score 0.5
    time "1688561602975"
  ]
  edge [
    source 0
    target 2
    key 0
    edge_name "file{path:/etc/mac.conf}"
    score 0.5
    time "1688561604967"
  ]
  edge [
    source 0
    target 3
    key 0
    edge_name "file{path:/etc/mac.conf}"
    score 0.5
    time "1688561605519"
  ]
  edge [
    source 0
    target 1
    key 0
    edge_name "file{path:/etc/mac.conf}"
    score 0.5
    time "1688561715390"
  ]
  edge [
    source 0
    target 6
    key 0
    edge_name "pipe_50_4_5"
    score 0.0
    time "1688561599661"
  ]
  edge [
    source 4
    target 2
    key 0
    edge_name "file{path:/etc/mac.conf}"
    score 0.5
    time "1688561600185"
  ]
]
