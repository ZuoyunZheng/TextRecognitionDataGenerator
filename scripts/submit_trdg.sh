rm data/trdg11 -r

parts=$(($1 / 10000))
echo "Splitting into $parts parts a la 10k samples"
for (( p=1; p<=$parts; p++ )); do
    echo "$p/$parts"
    source trdg.sh --output_dir data/trdg11/horizontal/lvis/$p -c 10000 -or 0 -b 3
done
