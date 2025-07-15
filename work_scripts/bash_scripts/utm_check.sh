#!/bin/bash

loc_ip=$(hostname -i)
podset=${loc_ip%.*}

IFS='.' read -ra ip228 <<< "$podset"
(( ip228[2] = ${ip228[2]}+3 ))
ip228="${ip228[0]}.${ip228[1]}.${ip228[2]}.228"

ip18="${podset}.18"

connectTimeOut=10
let checkCountDay=(86400 * 30)

pkiDateEnd=""
gostDateEnd=""
returnMessage="OK"
pkiDateNormalVisible=""
gostDateNormalVisible=""

loadData() {
    ip=$1
    port=$2

    pkiDateEnd=$(curl -s --connect-timeout $connectTimeOut http://$ip:$port/api/rsa/orginfo)
    gostDateEnd=$(curl -s --connect-timeout $connectTimeOut http://$ip:$port/api/gost/orginfo)

    # Если ответ содержит success:false или пустой — считаем, что данных нет
    if echo "$pkiDateEnd" | grep -q '"success":false'; then
        pkiDateEnd=""
    fi
    if echo "$gostDateEnd" | grep -q '"success":false'; then
        gostDateEnd=""
    fi

    if [ -n "$pkiDateEnd" ]; then
        origPKI=$pkiDateEnd
        pkiDateEnd=$(echo $pkiDateEnd | sed 's/.*to":"//g' | sed 's/\s.*//g')
        IFS='.' read -ra pkiDateArr <<< "$pkiDateEnd"
        pkiDateEnd=${pkiDateArr[2]}${pkiDateArr[1]}${pkiDateArr[0]}
        pkiDateNormalVisible=$origPKI
    fi

    if [ -n "$gostDateEnd" ]; then
        origGOST=$gostDateEnd
        gostDateEnd=$(echo $gostDateEnd | sed 's/.*to":"//g' | sed 's/\s.*//g')
        IFS='.' read -ra gostDateArr <<< "$gostDateEnd"
        gostDateEnd=${gostDateArr[2]}${gostDateArr[1]}${gostDateArr[0]}
        gostDateNormalVisible=$origGOST
    fi

}

checkDate() {
    currDate=$(date +%s -d $(date +%Y%m%d))
    pkiDateSec=$(date +%s -d $pkiDateEnd 2>/dev/null)
    gostDateSec=$(date +%s -d $gostDateEnd 2>/dev/null)

    let pkiCertLeft=($pkiDateSec-$currDate)
    let gostCertLeft=($gostDateSec-$currDate)

    if [ "$pkiCertLeft" -lt "$checkCountDay" ]; then
        returnMessage="Сертификат PKI заканчивается $pkiDateNormalVisible"
        if [ "$gostCertLeft" -lt "$checkCountDay" ]; then
            returnMessage="Сертификат PKI и ГОСТ заканчивается: PKI $pkiDateNormalVisible; ГОСТ $gostDateNormalVisible"
        fi
    else
        if [ "$gostCertLeft" -lt "$checkCountDay" ]; then
            returnMessage="Сертификат ГОСТ заканчивается $gostDateNormalVisible"
        fi
    fi
}

# === Основной блок ===
loadData $ip18 8080
if [ -z "$pkiDateEnd" ]; then
  loadData $ip228 8080
  if [ -z "$pkiDateEnd" ]; then
    loadData $ip18 8081
    if [ -z "$pkiDateEnd" ]; then
      loadData $ip228 8081
    fi
  fi
fi


if [ -z "$pkiDateEnd" ]; then
    returnMessage="УТМ нигде не доступен"
else
    checkDate
fi
echo "Результат"
echo -e $returnMessage