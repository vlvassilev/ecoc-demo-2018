#!/bin/bash -e

rm -rf tmp || true
mkdir tmp
if [ "$RUN_WITH_CONFD" != "" ] ; then
  cd tmp
  cp /usr/share/yuma/modules/transpacket/transpacket-fusion-streams.yang .
  cp /usr/share/yuma/modules/ietf/ietf-interfaces.yang .
  cp /usr/share/yuma/modules/ietf/iana-if-type.yang .
  cp /usr/share/yuma/modules/ietf-draft/ieee802-types@2016-07-24.yang .
  cp /usr/share/yuma/modules/ietf-draft/ieee802-dot1q-types@2016-09-22.yang .

  killall -KILL confd || true
  echo "Starting confd: $RUN_WITH_CONFD"
  source $RUN_WITH_CONFD/confdrc
  confdc -c ietf-interfaces.yang --yangpath . -o ietf-interfaces.fxs
  confdc -c iana-if-type.yang --yangpath . -o iana_if_type.fxs
  confdc -c ieee802-types@2016-07-24.yang --yangpath . -o ieee802-types@2016-07-24.fxs
  confdc -c ieee802-dot1q-types@2016-09-22.yang --yangpath . -o ieee802-dot1q-types@2016-09-22.fxs
  confdc -c transpacket-fusion-streams.yang --yangpath . -o transpacket-fusion-streams.fxs
  export NCSERVER=localhost
  export NCPORT=2022
  export NCUSER=admin
  export NCPASSWORD=admin
  confd --verbose --foreground --addloadpath ${RUN_WITH_CONFD}/src/confd --addloadpath ${RUN_WITH_CONFD}/src/confd --addloadpath ${RUN_WITH_CONFD}/src/confd/yang --addloadpath ${RUN_WITH_CONFD}/src/confd/aaa --addloadpath . 2>&1 1>server.log &
  SERVER_PID=$!
  cd ..
else
  killall -KILL netconfd || true
  rm /tmp/ncxserver.sock || true
  export NCSERVER=localhost
  export NCPORT=830
  export NCUSER=${USER}
  export NCPASSWORD=
  /usr/sbin/netconfd --module=/usr/share/yuma/modules/transpacket/transpacket-fusion-streams.yang --no-startup --superuser=$USER 2>&1 1>tmp/server.log &
  SERVER_PID=$!
fi

sleep 3
python session.local.yangcli.py
python session.remote.yangcli.py
#kill $SERVER_PID
cat tmp/server.log
sleep 1
