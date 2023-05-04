#!/bin/sh

if [ "$#" -ne 1 ]; then
    echo "usage: $0 #data-points"
    exit 1
fi

prog_dir="../analysis/flagged"
flag="O3"
data_points=$1

mkdir -p results

amount=$(find $prog_dir -type f | wc -l)
counter=1
for prog in $prog_dir/*; do 
    if [ -f "$prog" ]; then 
        name=$(basename $prog)
        seed=${name::-2}
        echo -e "Progress: $counter/$amount [$seed]"
        let counter=counter+1
        
        ./combine.sh $prog $flag 1>/dev/null 2>&1
        ./out "$data_points" $flag
        cp result.csv results/$seed.csv
    fi
done

rm out 1>/dev/null 2>&1
#rm result.csv
