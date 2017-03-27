#!/bin/bash

now=$(date +"%m%d%Y%H%M")
gogsconfiglocation=/home/git/gogs/custom/conf
rdsendpoint=$(aws rds describe-db-instances --query 'DBInstances[?DBName==`ent312demo`]' --output text | grep ENDPOINT | awk '{print $2":"$4}')

cp $gogsconfiglocation/app.ini $gogsconfiglocation/app.ini_$now.bak


sed -i '/HOST/s/= .*/= '"$rdsendpoint"'/' $gogsconfiglocation/app.ini
sed -i '/DOMAIN/s/= .*/= '"ent312.five0.ninja"'/' $gogsconfiglocation/app.ini
sed -i '/ROOT_URL/s/= .*/= '"http:\\/\\/ent312.five0.ninja\\/"'/' $gogsconfiglocation/app.ini

systemctl restart gogs

counter=1
while [ $counter -le 3 ]
    do
        if systemctl status gogs | grep running > /dev/null
            then
                echo Gogs Server is ready at: $(date)
                python /opt/CloudEndure_PostProcessing.py
                rm -rf /root/.aws
                rm -rf /home/centos/.aws2
                exit
        else
            echo Gogs Server is not ready. Sleeping for 10 seconds. Current time is: $(date)
            sleep 10
            ((counter++))
        fi
done

rm -rf /root/.aws
rm -rf /home/centos/.aws2