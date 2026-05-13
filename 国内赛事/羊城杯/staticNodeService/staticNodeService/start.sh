#!/bin/bash

if [ -n "$DASFLAG" ]; then
  echo $DASFLAG > /flag
else
  echo "DASFLAG 不存在,使用默认FLAG"
fi

su -c "node /App/App.js" node

