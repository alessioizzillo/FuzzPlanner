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
    label "/usr/etc/init.d/rcS"
    start_time "1688561599441"
    score 0.5
    is_proprietary 0
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
    label "/usr/script/wan_start.sh"
    start_time "1688561602423"
    score 4.65
    is_proprietary 1
  ]
  node [
    id 4
    label "/usr/script/ether_mac.sh"
    start_time "1688561605313"
    score 0.65
    is_proprietary 1
  ]
  node [
    id 5
    label "/bin/cat"
    start_time "1688561715108"
    score 0.0
    is_proprietary 0
  ]
  node [
    id 6
    label "/usr/script/wan_stop.sh"
    start_time "1688561712483"
    score 0.65
    is_proprietary 1
  ]
  node [
    id 7
    label "/bin/echo"
    start_time "1688561603448"
    score 0.0
    is_proprietary 0
  ]
  node [
    id 8
    label "<border>"
    score 0.0
    is_proprietary "<border>"
  ]
  node [
    id 9
    label "/sbin/init"
    start_time "1688561593426"
    score 0.15
    is_proprietary 0
  ]
  node [
    id 10
    label "/bin/mount"
    start_time "1688561593609"
    score 0.0
    is_proprietary 0
  ]
  node [
    id 11
    label "/bin/busybox"
    start_time "1688561593673"
    score 12.950000000000001
    is_proprietary 0
  ]
  node [
    id 12
    label "/userfs/bin/mtd"
    start_time "1688561595528"
    score 0.0
    is_proprietary 1
  ]
  node [
    id 13
    label "/usr/bin/iptables"
    start_time "1688561595623"
    score 0.0
    is_proprietary 0
  ]
  node [
    id 14
    label "/usr/bin/expr"
    start_time "1688561600272"
    score 0.0
    is_proprietary 0
  ]
  node [
    id 15
    label "/bin/sed"
    start_time "1688561599448"
    score 0.0
    is_proprietary 0
  ]
  node [
    id 16
    label "/userfs/bin/tcapi"
    start_time "1688561600487"
    score 0.0
    is_proprietary 1
  ]
  node [
    id 17
    label "/userfs/bin/boa"
    start_time "1688561600977"
    score 1.65
    is_proprietary 0
  ]
  node [
    id 18
    label "/usr/bin/ebtables"
    start_time "1688561605065"
    score 0.0
    is_proprietary 0
  ]
  node [
    id 19
    label "/userfs/bin/radvd"
    start_time "1688561610974"
    score 1.65
    is_proprietary 1
  ]
  node [
    id 20
    label "/userfs/bin/dhcp6s"
    start_time "1688561611110"
    score 0.5
    is_proprietary 1
  ]
  node [
    id 21
    label "/usr/sbin/udhcpd"
    start_time "1688561611179"
    score 1.0
    is_proprietary 0
  ]
  node [
    id 22
    label "/userfs/bin/dnsmasq"
    start_time "1688561611586"
    score 6.5
    is_proprietary 1
  ]
  node [
    id 23
    label "/usr/bin/killall"
    start_time "1688561611857"
    score 0.0
    is_proprietary 0
  ]
  node [
    id 24
    label "/userfs/bin/upnpd"
    start_time "1688561612462"
    score 2.5
    is_proprietary 1
  ]
  node [
    id 25
    label "/bin/pidof"
    start_time "1688561614766"
    score 0.0
    is_proprietary 0
  ]
  node [
    id 26
    label "/userfs/bin/inetd"
    start_time "1688561616645"
    score 0.5
    is_proprietary 0
  ]
  node [
    id 27
    label "/usr/script/fw_stop.sh"
    start_time "1688561721107"
    score 0.15
    is_proprietary 1
  ]
  node [
    id 28
    label "/usr/script/spi_fw_stop.sh"
    start_time "1688561721397"
    score 0.15
    is_proprietary 1
  ]
  node [
    id 29
    label "/userfs/bin/ntpclient"
    start_time "1688561721984"
    score 2.0
    is_proprietary 1
  ]
  node [
    id 30
    label "/usr/script/vserver.sh"
    start_time "1688561797209"
    score 0.15
    is_proprietary 1
  ]
  node [
    id 31
    label "/bin/hostname"
    start_time "1688561600576"
    score 0.0
    is_proprietary 0
  ]
  node [
    id 32
    label "/usr/bin/utelnetd"
    start_time "1688561600801"
    score 0.0
    is_proprietary 1
  ]
  edge [
    source 0
    target 1
    key 0
    edge_name "pipe_50_4_5"
    score 0.0
    time "1688561599559"
  ]
  edge [
    source 0
    target 3
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
    target 4
    key 0
    edge_name "file{path:/etc/mac.conf}"
    score 0.5
    time "1688561605519"
  ]
  edge [
    source 0
    target 6
    key 0
    edge_name "file{path:/etc/mac.conf}"
    score 0.5
    time "1688561715390"
  ]
  edge [
    source 0
    target 15
    key 0
    edge_name "pipe_50_4_5"
    score 0.0
    time "1688561599661"
  ]
  edge [
    source 1
    target 2
    key 0
    edge_name "file{path:/etc/mac.conf}"
    score 0.5
    time "1688561600185"
  ]
  edge [
    source 5
    target 6
    key 0
    edge_name "pipe_889_7_9"
    score 0.0
    time "1688561715160"
  ]
  edge [
    source 7
    target 5
    key 0
    edge_name "file{path:/var/run/nas0.pid}"
    score 0.0
    time "1688561715159"
  ]
  edge [
    source 7
    target 19
    key 0
    edge_name "virtual_file{path:/proc/sys/net/ipv6/conf/all/forwarding}"
    score 0.0
    time "1688561611038"
  ]
  edge [
    source 7
    target 31
    key 0
    edge_name "file{path:/etc/hostname}"
    score 0.0
    time "1688561600637"
  ]
  edge [
    source 8
    target 9
    key 0
    edge_name "file{path:/etc/TZ}"
    score 0.15
  ]
  edge [
    source 8
    target 9
    key 1
    edge_name "file{path:/usr/etc/inittab}"
    score 0.0
  ]
  edge [
    source 8
    target 1
    key 0
    edge_name "file{path:/usr/etc/init.d/rcS}"
    score 0.0
  ]
  edge [
    source 8
    target 1
    key 1
    edge_name "file{path:/userfs/profile.cfg}"
    score 0.5
  ]
  edge [
    source 8
    target 1
    key 2
    edge_name "file{path:/etc/Wireless/WLAN_APOn}"
    score 0.0
  ]
  edge [
    source 8
    target 10
    key 0
    edge_name "file{path:/usr/etc/fstab}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 0
    edge_name "file{path:/usr/etc/RT30xxEEPROM.bin}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 1
    edge_name "file{path:/usr/etc/Wireless/RT2860AP/RT2860AP.dat}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 2
    edge_name "file{path:/usr/etc/bftpd.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 3
    edge_name "file{path:/usr/etc/cert.pem}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 4
    edge_name "file{path:/usr/etc/defaultWan.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 5
    edge_name "device{path:/usr/etc/devInf.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 6
    edge_name "file{path:/usr/etc/dhcp6c.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 7
    edge_name "file{path:/usr/etc/dhcp6s.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 8
    edge_name "file{path:/usr/etc/dproxy.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 9
    edge_name "file{path:/usr/etc/ethertypes}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 10
    edge_name "file{path:/usr/etc/fwTCver.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 11
    edge_name "file{path:/usr/etc/fwTCver.conf~}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 12
    edge_name "file{path:/usr/etc/fwver.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 13
    edge_name "file{path:/usr/etc/fwver.conf~}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 14
    edge_name "file{path:/usr/etc/group}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 15
    edge_name "file{path:/usr/etc/hosts}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 16
    edge_name "file{path:/usr/etc/igd/gateconnSCPD.xml}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 17
    edge_name "file{path:/usr/etc/igd/gatedesc.xml}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 18
    edge_name "file{path:/usr/etc/igd/gateicfgSCPD.xml}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 19
    edge_name "file{path:/usr/etc/igd/gateinfoSCPD.xml}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 20
    edge_name "file{path:/usr/etc/igd/igd.sh}"
    score 0.15
  ]
  edge [
    source 8
    target 11
    key 21
    edge_name "file{path:/usr/etc/igd/portmap.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 22
    edge_name "file{path:/usr/etc/inetd.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 23
    edge_name "file{path:/usr/etc/inittab_no_ra_menu}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 24
    edge_name "file{path:/usr/etc/inittab_ra_menu}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 25
    edge_name "file{path:/usr/etc/iproute2/ematch_map}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 26
    edge_name "file{path:/usr/etc/iproute2/rt_dsfield}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 27
    edge_name "file{path:/usr/etc/iproute2/rt_protos}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 28
    edge_name "file{path:/usr/etc/iproute2/rt_realms}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 29
    edge_name "file{path:/usr/etc/iproute2/rt_scopes}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 30
    edge_name "file{path:/usr/etc/iproute2/rt_tables}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 31
    edge_name "file{path:/usr/etc/key.pem}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 32
    edge_name "file{path:/usr/etc/l7-protocols/aim.pat}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 33
    edge_name "file{path:/usr/etc/l7-protocols/msnmessenger.pat}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 34
    edge_name "file{path:/usr/etc/l7-protocols/rtp.pat}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 35
    edge_name "file{path:/usr/etc/l7-protocols/rtsp.pat}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 36
    edge_name "file{path:/usr/etc/l7-protocols/yahoo.pat}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 37
    edge_name "file{path:/usr/etc/passwd}"
    score 0.15
  ]
  edge [
    source 8
    target 11
    key 38
    edge_name "file{path:/usr/etc/ppp/ipv6-up}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 39
    edge_name "file{path:/usr/etc/ppp/peers/ppp_connect}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 40
    edge_name "file{path:/usr/etc/ppp/peers/ppp_on_dialer.sh}"
    score 0.15
  ]
  edge [
    source 8
    target 11
    key 41
    edge_name "file{path:/usr/etc/ppp/peers/wcdma}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 42
    edge_name "file{path:/usr/etc/protocols}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 43
    edge_name "file{path:/usr/etc/radvd.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 44
    edge_name "file{path:/usr/etc/resolv.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 45
    edge_name "file{path:/usr/etc/resolv_ipv4.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 46
    edge_name "file{path:/usr/etc/resolv_ipv6.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 47
    edge_name "file{path:/usr/etc/services}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 48
    edge_name "file{path:/usr/etc/snmp/snmpd.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 49
    edge_name "file{path:/usr/etc/snmpd.conf.tmp}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 50
    edge_name "virtual_file{path:/usr/etc/sysconfig/network}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 51
    edge_name "file{path:/usr/etc/trx_config}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 52
    edge_name "file{path:/usr/etc/usertty}"
    score 0.0
  ]
  edge [
    source 8
    target 11
    key 53
    edge_name "file{path:/usr/etc/voip_sys.cfg}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 54
    edge_name "file{path:/usr/etc/xml/WFADeviceDesc.xml}"
    score 0.5
  ]
  edge [
    source 8
    target 11
    key 55
    edge_name "file{path:/usr/etc/xml/WFAWLANConfigSCPD.xml}"
    score 0.5
  ]
  edge [
    source 8
    target 12
    key 0
    edge_name "virtual_file{path:/proc/mtd}"
    score 0.0
  ]
  edge [
    source 8
    target 13
    key 0
    edge_name "virtual_file{path:/proc/sys/kernel/modprobe}"
    score 0.0
  ]
  edge [
    source 8
    target 5
    key 0
    edge_name "device{path:/dev/mtd0}"
    score 0.0
  ]
  edge [
    source 8
    target 0
    key 0
    edge_name "virtual_file{path:/proc/sys/net/ipv6/conf/lo/disable_ipv6}"
    score 0.0
  ]
  edge [
    source 8
    target 0
    key 1
    edge_name "virtual_file{path:/proc/sys/net/ipv6/conf/eth0/disable_ipv6}"
    score 0.0
  ]
  edge [
    source 8
    target 0
    key 2
    edge_name "virtual_file{path:/proc/net/dev}"
    score 0.5
  ]
  edge [
    source 8
    target 0
    key 3
    edge_name "virtual_file{path:/proc/net/if_inet6}"
    score 0.15
  ]
  edge [
    source 8
    target 0
    key 4
    edge_name "virtual_file{path:/proc/sys/net/ipv6/conf/br0/disable_ipv6}"
    score 0.15
  ]
  edge [
    source 8
    target 2
    key 0
    edge_name "file{path:/usr/script/br_conf.sh}"
    score 0.15
  ]
  edge [
    source 8
    target 2
    key 1
    edge_name "file{path:/etc/lanconfig.sh}"
    score 0.15
  ]
  edge [
    source 8
    target 2
    key 2
    edge_name "file{path:/etc/adsl.sh}"
    score 0.15
  ]
  edge [
    source 8
    target 2
    key 3
    edge_name "file{path:/usr/script/filter_forward_start.sh}"
    score 0.15
  ]
  edge [
    source 8
    target 2
    key 4
    edge_name "file{path:/tmp/etc/acl.sh}"
    score 0.15
  ]
  edge [
    source 8
    target 2
    key 5
    edge_name "file{path:/etc/autoexec.sh}"
    score 0.15
  ]
  edge [
    source 8
    target 2
    key 6
    edge_name "file{path:/usr/script/ipmacfilter_stop.sh}"
    score 0.15
  ]
  edge [
    source 8
    target 2
    key 7
    edge_name "file{path:/etc/ntp.sh}"
    score 0.15
  ]
  edge [
    source 8
    target 17
    key 0
    edge_name "file{path:boa.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 17
    key 1
    edge_name "file{path:/etc/passwd}"
    score 0.15
  ]
  edge [
    source 8
    target 17
    key 2
    edge_name "file{path:/etc/group}"
    score 0.0
  ]
  edge [
    source 8
    target 17
    key 3
    edge_name "socket(domain:10, type:2, protocol:6){addr:0.65.139.180; port:80}"
    score 1.0
  ]
  edge [
    source 8
    target 17
    key 4
    edge_name "file{path:/boaroot/cgi-bin/index.asp}"
    score 0.0
  ]
  edge [
    source 8
    target 17
    key 5
    edge_name "file{path:/boaroot/cgi-bin/login.asp}"
    score 0.0
  ]
  edge [
    source 8
    target 17
    key 6
    edge_name "file{path:/boaroot/cgi-bin/wan.asp}"
    score 0.0
  ]
  edge [
    source 8
    target 17
    key 7
    edge_name "file{path:/boaroot/cgi-bin/menu.asp}"
    score 0.0
  ]
  edge [
    source 8
    target 17
    key 8
    edge_name "file{path:/boaroot/cgi-bin/euhelp.asp}"
    score 0.0
  ]
  edge [
    source 8
    target 17
    key 9
    edge_name "file{path:/boaroot/cgi-bin/Wizard.asp}"
    score 0.0
  ]
  edge [
    source 8
    target 17
    key 10
    edge_name "file{path:/boaroot/cgi-bin/portforwarding.asp}"
    score 0.0
  ]
  edge [
    source 8
    target 17
    key 11
    edge_name "file{path:/boaroot/cgi-bin/advhelp.asp}"
    score 0.0
  ]
  edge [
    source 8
    target 3
    key 0
    edge_name "file{path:/usr/script/wan_start.sh}"
    score 0.15
  ]
  edge [
    source 8
    target 3
    key 1
    edge_name "file{path:/etc/isp0.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 3
    key 2
    edge_name "file{path:/etc/isp1.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 3
    key 3
    edge_name "file{path:/etc/isp2.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 3
    key 4
    edge_name "file{path:/etc/isp3.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 3
    key 5
    edge_name "file{path:/etc/isp4.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 3
    key 6
    edge_name "file{path:/etc/isp5.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 3
    key 7
    edge_name "file{path:/etc/isp6.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 3
    key 8
    edge_name "file{path:/etc/isp7.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 18
    key 0
    edge_name "file{path:/etc/ethertypes}"
    score 0.0
  ]
  edge [
    source 8
    target 4
    key 0
    edge_name "file{path:/usr/script/ether_mac.sh}"
    score 0.15
  ]
  edge [
    source 8
    target 19
    key 0
    edge_name "file{path:/etc/radvd.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 19
    key 1
    edge_name "virtual_file{path:/proc/net/igmp6}"
    score 0.15
  ]
  edge [
    source 8
    target 19
    key 2
    edge_name "socket(domain:10, type:3, protocol:58){addr:0.0.0.0; port:0}"
    score 1.0
  ]
  edge [
    source 8
    target 20
    key 0
    edge_name "file{path:/etc/dhcp6s.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 21
    key 0
    edge_name "file{path:/etc/udhcpd.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 21
    key 1
    edge_name "file{path:/etc/udhcpd_option.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 22
    key 0
    edge_name "device{path:/dev/urandom}"
    score 0.0
  ]
  edge [
    source 8
    target 22
    key 1
    edge_name "file{path:/etc/resolv.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 22
    key 2
    edge_name "file{path:/etc/hosts}"
    score 0.0
  ]
  edge [
    source 8
    target 22
    key 3
    edge_name "socket(domain:16, type:3, protocol:0){pid:0; groups:1024}"
    score 0.0
  ]
  edge [
    source 8
    target 22
    key 4
    edge_name "socket(domain:16, type:3, protocol:0){pid:0; groups:64}"
    score 0.0
  ]
  edge [
    source 8
    target 22
    key 5
    edge_name "socket(domain:2, type:1, protocol:0){addr:127.0.0.1; port:39764}"
    score 1.0
  ]
  edge [
    source 8
    target 22
    key 6
    edge_name "socket(domain:10, type:1, protocol:0){addr:0.0.0.0; port:37330}"
    score 1.0
  ]
  edge [
    source 8
    target 22
    key 7
    edge_name "socket(domain:2, type:1, protocol:0){addr:127.0.0.1; port:35309}"
    score 1.0
  ]
  edge [
    source 8
    target 22
    key 8
    edge_name "socket(domain:10, type:1, protocol:0){addr:0.0.0.0; port:58678}"
    score 1.0
  ]
  edge [
    source 8
    target 22
    key 9
    edge_name "socket(domain:2, type:1, protocol:0){addr:127.0.0.1; port:35306}"
    score 1.0
  ]
  edge [
    source 8
    target 22
    key 10
    edge_name "socket(domain:10, type:1, protocol:0){addr:0.0.0.0; port:54999}"
    score 1.0
  ]
  edge [
    source 8
    target 23
    key 0
    edge_name "virtual_file{path:/proc/1/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 1
    edge_name "virtual_file{path:/proc/2/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 2
    edge_name "virtual_file{path:/proc/3/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 3
    edge_name "virtual_file{path:/proc/4/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 4
    edge_name "virtual_file{path:/proc/5/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 5
    edge_name "virtual_file{path:/proc/6/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 6
    edge_name "virtual_file{path:/proc/7/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 7
    edge_name "virtual_file{path:/proc/8/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 8
    edge_name "virtual_file{path:/proc/9/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 9
    edge_name "virtual_file{path:/proc/10/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 10
    edge_name "virtual_file{path:/proc/11/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 11
    edge_name "virtual_file{path:/proc/12/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 12
    edge_name "virtual_file{path:/proc/13/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 13
    edge_name "virtual_file{path:/proc/14/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 14
    edge_name "virtual_file{path:/proc/15/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 15
    edge_name "virtual_file{path:/proc/16/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 16
    edge_name "virtual_file{path:/proc/17/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 17
    edge_name "virtual_file{path:/proc/18/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 18
    edge_name "virtual_file{path:/proc/35/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 19
    edge_name "virtual_file{path:/proc/36/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 20
    edge_name "virtual_file{path:/proc/37/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 21
    edge_name "virtual_file{path:/proc/38/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 22
    edge_name "virtual_file{path:/proc/39/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 23
    edge_name "virtual_file{path:/proc/40/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 24
    edge_name "virtual_file{path:/proc/41/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 25
    edge_name "virtual_file{path:/proc/44/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 26
    edge_name "virtual_file{path:/proc/45/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 27
    edge_name "virtual_file{path:/proc/46/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 28
    edge_name "virtual_file{path:/proc/47/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 29
    edge_name "virtual_file{path:/proc/49/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 30
    edge_name "virtual_file{path:/proc/50/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 31
    edge_name "virtual_file{path:/proc/54/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 32
    edge_name "virtual_file{path:/proc/57/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 33
    edge_name "virtual_file{path:/proc/91/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 34
    edge_name "virtual_file{path:/proc/93/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 35
    edge_name "virtual_file{path:/proc/94/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 36
    edge_name "virtual_file{path:/proc/243/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 37
    edge_name "virtual_file{path:/proc/245/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 38
    edge_name "virtual_file{path:/proc/249/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 39
    edge_name "virtual_file{path:/proc/257/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 40
    edge_name "virtual_file{path:/proc/399/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 41
    edge_name "virtual_file{path:/proc/401/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 42
    edge_name "virtual_file{path:/proc/559/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 43
    edge_name "virtual_file{path:/proc/563/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 44
    edge_name "virtual_file{path:/proc/565/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 45
    edge_name "virtual_file{path:/proc/567/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 46
    edge_name "virtual_file{path:/proc/568/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 47
    edge_name "virtual_file{path:/proc/570/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 48
    edge_name "virtual_file{path:/proc/571/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 49
    edge_name "virtual_file{path:/proc/574/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 50
    edge_name "virtual_file{path:/proc/576/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 51
    edge_name "virtual_file{path:/proc/579/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 52
    edge_name "virtual_file{path:/proc/580/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 53
    edge_name "virtual_file{path:/proc/583/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 54
    edge_name "virtual_file{path:/proc/584/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 55
    edge_name "virtual_file{path:/proc/586/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 56
    edge_name "virtual_file{path:/proc/609/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 57
    edge_name "virtual_file{path:/proc/759/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 58
    edge_name "virtual_file{path:/proc/760/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 59
    edge_name "virtual_file{path:/proc/798/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 60
    edge_name "virtual_file{path:/proc/801/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 61
    edge_name "virtual_file{path:/proc/807/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 62
    edge_name "virtual_file{path:/proc/808/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 63
    edge_name "virtual_file{path:/proc/810/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 64
    edge_name "virtual_file{path:/proc/816/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 65
    edge_name "virtual_file{path:/proc/1054/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 66
    edge_name "virtual_file{path:/proc/1106/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 67
    edge_name "virtual_file{path:/proc/1112/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 68
    edge_name "virtual_file{path:/proc/1227/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 23
    key 69
    edge_name "virtual_file{path:/proc/1228/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 24
    key 0
    edge_name "file{path:/etc/igd/igd.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 24
    key 1
    edge_name "file{path:/etc/igd/gatedesc.xml}"
    score 0.5
  ]
  edge [
    source 8
    target 24
    key 2
    edge_name "file{path:/etc/igd/portmap.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 24
    key 3
    edge_name "socket(domain:2, type:1, protocol:0){addr:192.168.1.2; port:55748}"
    score 1.0
  ]
  edge [
    source 8
    target 25
    key 0
    edge_name "virtual_file{path:/proc/761/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 25
    key 1
    edge_name "virtual_file{path:/proc/762/stat}"
    score 0.0
  ]
  edge [
    source 8
    target 26
    key 0
    edge_name "file{path:/etc/inetd.conf}"
    score 0.5
  ]
  edge [
    source 8
    target 26
    key 1
    edge_name "file{path:/etc/services}"
    score 0.0
  ]
  edge [
    source 8
    target 6
    key 0
    edge_name "file{path:/usr/script/wan_stop.sh}"
    score 0.15
  ]
  edge [
    source 8
    target 27
    key 0
    edge_name "file{path:/usr/script/fw_stop.sh}"
    score 0.15
  ]
  edge [
    source 8
    target 28
    key 0
    edge_name "file{path:/usr/script/spi_fw_stop.sh}"
    score 0.15
  ]
  edge [
    source 8
    target 29
    key 0
    edge_name "socket(domain:2, type:1, protocol:17){addr:127.0.0.1; port:53}"
    score 1.0
  ]
  edge [
    source 8
    target 29
    key 1
    edge_name "socket(domain:10, type:1, protocol:17){addr:127.0.0.1; port:53}"
    score 1.0
  ]
  edge [
    source 8
    target 30
    key 0
    edge_name "file{path:/usr/script/vserver.sh}"
    score 0.15
  ]
  edge [
    source 8
    target 30
    key 1
    edge_name "file{path:/etc/nat_pvc0/vserver0}"
    score 0.0
  ]
  edge [
    source 8
    target 30
    key 2
    edge_name "file{path:/etc/nat_pvc0/ipmode}"
    score 0.0
  ]
  edge [
    source 14
    target 15
    key 0
    edge_name "pipe_50_3_4"
    score 0.0
    time "1688561599550"
  ]
  edge [
    source 16
    target 15
    key 0
    edge_name "pipe_50_3_4"
    score 0.0
    time "1688561599550"
  ]
  edge [
    source 22
    target 22
    key 0
    edge_name "pipe_578_8_9"
    score 0.0
    time "1688561611714"
  ]
]
