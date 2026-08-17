#include "config.h"
#include "BytecodeStructs.h"
#include "CodeBlock.h"
#include <cstdio>
using namespace JSC;
#define M(Op) printf("%-32s meta=%3zu instrSize(wide32)=%3zu\n", #Op, sizeof(Op::Metadata), sizeof(Op))
int main(){
  M(OpTailCallVarargs);
  M(OpCallVarargs);
  M(OpIteratorNext);
  M(OpConstructVarargs);
  M(OpSuperConstructVarargs);
  M(OpIteratorOpen);
  M(OpAsyncIteratorOpen);
  M(OpInstanceof);
  M(OpSetPrivateBrand);
  M(OpCheckPrivateBrand);
  M(OpPutById);
  M(OpConstruct);
  M(OpSuperConstruct);
  M(OpTailCall);
  M(OpCallDirectEval);
  M(OpCreateGenerator);
  M(OpCreateAsyncGenerator);
  M(OpCreatePromise);
  M(OpCatch);
  M(OpNewArrayWithSize);
  M(OpNewArrayBuffer);
  M(OpGetById);
  M(OpGetLength);
  M(OpProfileType);
  M(OpProfileControlFlow);
  M(OpNewArrayWithSpecies);
  M(OpCall);
  M(OpCallIgnoreResult);
  M(OpAsyncIteratorNext);
  M(OpResolveScope);
  M(OpGetFromScope);
  M(OpPutToScope);
  M(OpCreateThis);
  M(OpNewObject);
  M(OpNewArray);
  M(OpPutPrivateName);
  M(OpGetPrivateName);
  M(OpGetByValWithThis);
  M(OpGetByVal);
  M(OpPutByVal);
  M(OpPutByValDirect);
  M(OpInByVal);
  M(OpEnumeratorNext);
  M(OpEnumeratorInByVal);
  M(OpEnumeratorHasOwnProperty);
  M(OpEnumeratorPutByVal);
  M(OpToThis);
  M(OpEnumeratorGetByVal);
  M(OpGetByIdDirect);
  M(OpJneqPtr);
  printf("ValueProfile=%zu ArrayProfile=%zu\n", sizeof(ValueProfile), sizeof(ArrayProfile));
  return 0;
}
