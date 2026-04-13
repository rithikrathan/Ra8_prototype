#!/bin/bash

cd "$(dirname "$0")/.."

ASSEMBLER="./assembler"
PASS=0
FAIL=0

echo "========================================="
echo "     ASSEMBLER TEST SUITE"
echo "========================================="
echo ""

for testfile in testScripts/*.asm; do
    testname=$(basename "$testfile")
    echo "Running: $testname"
    
    output=$($ASSEMBLER "$testfile" 2>&1)
    exitcode=$?
    
    echo "$output" > "testScripts/output_${testname%.asm}.txt"
    
    if [[ "$testname" == 09_duplicate_label.asm ]] || \
       [[ "$testname" == 10_undefined_label.asm ]] || \
       [[ "$testname" == 11_wrong_operands.asm ]] || \
       [[ "$testname" == 12_invalid_identifier.asm ]]; then
        if [[ "$exitcode" -ne 0 ]] || [[ "$output" == *"SEMANTIC"* ]] || [[ "$output" == *"Error"* ]]; then
            echo "  [PASS] Error detected correctly"
            ((PASS++))
        else
            echo "  [FAIL] Expected semantic error"
            ((FAIL++))
        fi
    else
        if [[ "$exitcode" -eq 0 ]]; then
            echo "  [PASS] Parsed successfully"
            ((PASS++))
        else
            echo "  [FAIL] Failed to parse"
            ((FAIL++))
        fi
    fi
    echo ""
done

echo "========================================="
echo "Results: $PASS passed, $FAIL failed"
echo "========================================="

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
exit 0