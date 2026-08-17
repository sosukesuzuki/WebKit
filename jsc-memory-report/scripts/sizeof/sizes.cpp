#include "config.h"
#include "CodeBlock.h"
#include "UnlinkedCodeBlock.h"
#include "UnlinkedFunctionCodeBlock.h"
#include "MetadataTable.h"
#include "UnlinkedMetadataTable.h"
#include "ValueProfile.h"
#include "ArrayProfile.h"
#include "ArithProfile.h"
#include "PropertyInlineCache.h"
#include "InlineCacheHandler.h"
#include "SharedJITStubSet.h"
#include "LazyValueProfile.h"
#include "PropertyInlineCacheClearingWatchpoint.h"
#include "AccessCase.h"
#include "GetterSetterAccessCase.h"
#include "ProxyableAccessCase.h"
#include "IntrinsicGetterAccessCase.h"
#include "InlineCacheCompiler.h"
#include "CallLinkInfo.h"
#include "PolymorphicCallStubRoutine.h"
#include "JITMathIC.h"
#include "JITAddGenerator.h"
#include "JITMulGenerator.h"
#include "JITSubGenerator.h"
#include "JITNegGenerator.h"
#include "DFGNode.h"
#include "DFGAbstractValue.h"
#include "DFGBasicBlock.h"
#include "DFGOSRExit.h"
#include "DFGJITCode.h"
#include "DFGCommonData.h"
#include "DFGVariableEventStream.h"
#include "DFGMinifiedNode.h"
#include "DFGOSREntry.h"
#include "DFGVariableAccessData.h"
#include "DFGGraph.h"
#include "DFGAdaptiveStructureWatchpoint.h"
#include "DFGAdaptiveInferredPropertyValueWatchpoint.h"
#include "FTLOSRExit.h"
#include "FTLJITCode.h"
#include "FTLExitValue.h"
#include "InlineCallFrame.h"
#include "CodeOrigin.h"
#include "ValueRecovery.h"
#include "MethodOfGettingAValueProfile.h"
#include "Watchpoint.h"
#include "CodeBlockJettisoningWatchpoint.h"
#include "ObjectPropertyCondition.h"
#include "ObjectPropertyConditionSet.h"
#include "Structure.h"
#include "StructureRareData.h"
#include "PropertyTable.h"
#include "JSObject.h"
#include "JSFunction.h"
#include "FunctionRareData.h"
#include "ObjectAllocationProfile.h"
#include "WeakImpl.h"
#include "JITCode.h"
#include "BaselineJITCode.h"
#include "JITCodeMap.h"
#include "JITStubRoutine.h"
#include "GCAwareJITStubRoutine.h"
#include "B3Value.h"
#include "AirInst.h"
#include "B3BasicBlock.h"
#include "ExpressionInfo.h"
#include "JumpTable.h"
#include "DFGExitProfile.h"
#include "JITStubRoutineSet.h"
#include "MarkedBlock.h"
#include "ExecutableMemoryHandle.h"
#include "LinkBuffer.h"
#include "MacroAssemblerCodeRef.h"
#include "FunctionExecutable.h"
#include "JSGlobalObject.h"
#include "StructureTransitionTable.h"
#include "InstructionStream.h"
#include "CacheableIdentifier.h"
#include "GetByStatus.h"
#include "PutByStatus.h"
#include "CallLinkStatus.h"
#include "DFGDesiredWatchpoints.h"
#include "PCToCodeOriginMap.h"
#include "ProfilerCompilation.h"
#include <cstdio>

using namespace JSC;
#define P(T) printf("%-56s %6zu\n", #T, sizeof(T))
int main() {
  P(CodeBlock); P(UnlinkedCodeBlock); P(UnlinkedFunctionCodeBlock); P(CodeBlock::RareData); P(DFG::JITData); P(BaselineJITData);
  P(MetadataTable); P(UnlinkedMetadataTable);
  P(ValueProfile); P(ArgumentValueProfile); P(ArrayProfile); P(UnlinkedArrayProfile); P(BinaryArithProfile); P(UnaryArithProfile);
  P(PropertyInlineCache); P(HandlerPropertyInlineCache); P(RepatchingPropertyInlineCache); P(UnlinkedPropertyInlineCache); P(BaselineUnlinkedPropertyInlineCache); P(PropertyInlineCacheClearingWatchpoint); P(CompressedLazyValueProfileHolder);
  P(AccessCase); P(GetterSetterAccessCase); P(ProxyableAccessCase); P(IntrinsicGetterAccessCase); P(PolymorphicAccess); P(InlineCacheHandler);
  P(CallLinkInfo); P(OptimizingCallLinkInfo); P(DataOnlyCallLinkInfo); P(DirectCallLinkInfo); P(UnlinkedCallLinkInfo);
  P(PolymorphicCallStubRoutine); P(CallSlot);
  P(JITAddIC); P(JITMulIC); P(JITSubIC); P(JITNegIC);
  P(DFG::Node); P(DFG::AbstractValue); P(DFG::StructureAbstractValue); P(DFG::BasicBlock); P(DFG::OSRExit); P(DFG::OSRExitBase);
  P(DFG::JITCode); P(DFG::CommonData); P(DFG::VariableEvent); P(DFG::MinifiedNode); P(DFG::OSREntryData); P(DFG::VariableAccessData); P(DFG::Graph);
  P(DFG::AdaptiveStructureWatchpoint); P(DFG::AdaptiveInferredPropertyValueWatchpoint);
  P(FTL::OSRExit); P(FTL::OSRExitDescriptor); P(FTL::JITCode); P(FTL::ExitValue);
  P(InlineCallFrame); P(CodeOrigin); P(ValueRecovery); P(MethodOfGettingAValueProfile);
  P(Watchpoint); P(WatchpointSet); P(InlineWatchpointSet); P(CodeBlockJettisoningWatchpoint);
  P(ObjectPropertyCondition); P(ObjectPropertyConditionSet); P(PropertyCondition);
  P(Structure); P(StructureRareData); P(PropertyTable); P(JSObject); P(JSFunction); P(FunctionRareData); P(ObjectAllocationProfile); P(WeakImpl);
  P(JITCode); P(DirectJITCode); P(NativeJITCode); P(BaselineJITCode); P(JITCodeMap); P(JITStubRoutine); P(GCAwareJITStubRoutine); P(PolymorphicAccessJITStubRoutine);
  P(B3::Value); P(B3::Air::Inst); P(B3::Air::Arg); P(B3::BasicBlock);
  P(ExpressionInfo); P(SimpleJumpTable); P(UnlinkedSimpleJumpTable); P(StringJumpTable); P(UnlinkedStringJumpTable);
  P(DFG::ExitProfile); P(DFG::FrequentExitSite);
  P(JITStubRoutineSet); P(MarkedBlock); P(ExecutableMemoryHandle); P(LinkBuffer); P(MacroAssemblerCodeRef<JITCompilationPtrTag>);
  P(FunctionExecutable); P(ScriptExecutable); P(StructureTransitionTable); P(CacheableIdentifier); P(GetByStatus); P(GetByVariant); P(PutByStatus); P(CallLinkStatus); P(CallVariant);
  P(DFG::DesiredWatchpoints); P(PCToCodeOriginMap); P(JSGlobalObject); P(Butterfly); P(IndexingHeader); P(JSCell);
  return 0;
}
