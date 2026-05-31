for i in `seq 1 10` ; do
    ./jsm4s/target/universal/stage/bin/jsm-cli split 5 ./spark.fimi ./train.fimi ./verify.fimi
    ./jsm4s/target/universal/stage/bin/jsm-cli tau ./verify.fimi ./tau.fimi
    ./jsm4s/target/universal/stage/bin/jsm-cli generate -m ./model.fimi -a cbo --strategy=boundedVotingMajority:50 ./train.fimi
    ./jsm4s/target/universal/stage/bin/jsm-cli predict  -m ./model.fimi -o ./predictions.fimi ./tau.fimi
    ./jsm4s/target/universal/stage/bin/jsm-cli stats ./verify.fimi ./predictions.fimi
done | grep Correct | awk '{ x += int(substr($7, 1, length($7)-1)); } END { print x / 10.0 }'