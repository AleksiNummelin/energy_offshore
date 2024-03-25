#!/bin/bash

#levtype="o2d"
#vars=("avg_sithick" "avg_siconc" "avg_siue" "avg_sivn" "avg_tos" "avg_sos" "avg_zos")
#monthlymeanvars=("avg_sithick" "avg_siconc")
#monthlymaxvars=("avg_sithick" "avg_siconc")
#treshvars=("avg_sithick" "avg_siconc")
#tresh=(0.1 0.15)

# levtype="sfc"

vars_sfc=("10u" "10v" "2t" "2d" "tprate")
vars_hl=("100u" "100v")
vars_o2d=("avg_sithick" "avg_siconc" "avg_siue" "avg_sivn" "avg_tos" "avg_sos" "avg_zos")

# numstats=$(( ${#vars[@]} + ${#monthlymeanvars[@]} + ${#monthlymaxvars[@]} + ${#treshvars[@]}))



REQUEST=request.yml



cat > $REQUEST <<EOF
ENERGY_OFFSHORE:
EOF


numstat=1

for i in $(seq 0 $(( ${#vars_sfc[@]} - 1)) )
do
cat >> $REQUEST <<EOF
    $numstat:
      GSVREQUEST:
        dataset: climate-dt
        class: d1
        type: fc
        expver: "%APP.READ_EXPID%"
        stream: clte
        activity: HighResMIP
        resolution: high
        generation: 1
        realization: 1
        experiment: cont
        model: IFS-NEMO
        levtype: "sfc"
        date: split_day
        time: "0000/to/2300/by/0100"
        param: "${vars_sfc[$i]}"
        grid: "0.1/0.1"
        area: "70/-12/48/31"
        method: nn

      OPAREQUEST:
        variable: "${vars_sfc[$i]}"
        stat: "raw"
        stat_freq: "hourly"
        time_step: 60 # in minutes, 60*timestep length in hours TODO: ...
        save: True
        checkpoint: True
        checkpoint_filepath: "%APP.OUTPATH%"
        save_filepath: "%APP.OUTPATH%"

EOF
 numstat=$(( $numstat + 1 ))
done


for i in $(seq 0 $(( ${#vars_hl[@]} - 1)) )
do
cat >> $REQUEST <<EOF
    $numstat:
      GSVREQUEST:
        dataset: climate-dt
        class: d1
        type: fc
        expver: "%APP.READ_EXPID%"
        stream: clte
        activity: HighResMIP
        resolution: high
        generation: 1
        realization: 1
        experiment: cont
        model: IFS-NEMO
        levtype: "hl"
        levelist: "100"
        date: split_day
        time: "0000/to/2300/by/0100"
        param: "${vars_hl[$i]}"
        grid: "0.1/0.1"
        area: "70/-12/48/31"
        method: nn

      OPAREQUEST:
        variable: "${vars_hl[$i]}"
        stat: "raw"
        stat_freq: "hourly"
        time_step: 60 # in minutes, 60*timestep length in hours TODO: ...
        save: True
        checkpoint: True
        checkpoint_filepath: "%APP.OUTPATH%"
        save_filepath: "%APP.OUTPATH%"

EOF
 numstat=$(( $numstat + 1 ))
done


for i in $(seq 0 $(( ${#vars_o2d[@]} - 1)) )
do
cat >> $REQUEST <<EOF
    $numstat:
      GSVREQUEST:
        dataset: climate-dt
        class: d1
        type: fc
        expver: "%APP.READ_EXPID%"
        stream: clte
        activity: HighResMIP
        resolution: high
        generation: 1
        realization: 1
        experiment: cont
        model: IFS-NEMO
        levtype: "o2d"
        date: split_day
        time: "0000"
        param: "${vars_o2d[$i]}"
        grid: "0.1/0.1"
        area: "70/-12/48/31"
        method: nn

      OPAREQUEST:
        variable: "${vars_o2d[$i]}"
        stat: "raw"
        stat_freq: "daily"
        time_step: 60 # in minutes, 60*timestep length in hours TODO: ...
        save: True
        checkpoint: True
        checkpoint_filepath: "%APP.OUTPATH%"
        save_filepath: "%APP.OUTPATH%"

EOF
 numstat=$(( $numstat + 1 ))
done
