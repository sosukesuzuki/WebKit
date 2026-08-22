#!/bin/bash
# usage: genops.sh <webkit-sha> -> writes /tmp/ops-<sha>.txt (opcode name -> id for ops with metadata) using that version's generator
sha=$1; d=/tmp/gen-$sha; mkdir -p $d/generator $d/bytecode $d/wasm $d/out
base="https://raw.githubusercontent.com/oven-sh/WebKit/$sha/Source/JavaScriptCore"
for f in Argument.rb Assertion.rb Checkpoints.rb DSL.rb Fits.rb GeneratedFile.rb Metadata.rb Opcode.rb OpcodeGroup.rb Options.rb Section.rb Template.rb Type.rb Wasm.rb main.rb; do curl -sS "$base/generator/$f" -o $d/generator/$f; done
curl -sS "$base/bytecode/BytecodeList.rb" -o $d/bytecode/BytecodeList.rb
curl -sS "$base/wasm/wasm.json" -o $d/wasm/wasm.json
ruby $d/generator/main.rb --bytecodes_h $d/out/Bytecodes.h --init_bytecodes_asm $d/out/InitBytecodes.asm --bytecode_structs_h $d/out/BytecodeStructs.h --bytecode_indices_h $d/out/BytecodeIndices.h $d/bytecode/BytecodeList.rb --wasm_json $d/wasm/wasm.json --bytecode_dumper $d/out/BytecodeDumperGenerated.cpp 2>&1 | tail -2
grep -n "NUMBER_OF_BYTECODE_WITH_METADATA" $d/out/Bytecodes.h | head -1
awk '/macro\(op_[a-z_0-9]+, [0-9]+\)/{gsub(/[(),\\]/," "); print $2}' $d/out/Bytecodes.h | head -60 | awk '{print NR-1, $1}' > /tmp/ops-$sha.txt
grep -n "op_call \|op_call$\| op_construct$\| op_iterator_open$" /tmp/ops-$sha.txt | head
