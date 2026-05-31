./jsm4s/target/universal/stage/bin/jsm-cli split 8:2 ./spark.fimi ./train.fimi ./verify.fimi
./jsm4s/target/universal/stage/bin/jsm-cli tau ./verify.fimi ./tau.fimi
./jsm4s/target/universal/stage/bin/jsm-cli generate -m ./model.fimi -a cbo --strategy=boundedVotingMajority:20 ./train.fimi
./jsm4s/target/universal/stage/bin/jsm-cli predict  -m ./model.fimi -o ./predictions.fimi ./tau.fimi
./jsm4s/target/universal/stage/bin/jsm-cli stats ./verify.fimi ./predictions.fimi