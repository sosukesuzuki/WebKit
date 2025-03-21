/*
 * Copyright (C) 2015-2023 Apple Inc. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY APPLE INC. ``AS IS'' AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL APPLE INC. OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 * PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
 * OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 
 */

#pragma once

#if ENABLE(B3_JIT)

#include "AirArg.h"
#include "AirSpecial.h"
#include "B3ValueRep.h"
#include <wtf/SequesteredMalloc.h>
#include <wtf/TZoneMalloc.h>

namespace JSC { namespace B3 {

namespace Air { class Code; }

// This is a base class for specials that have stackmaps. Note that it can find the Stackmap by
// asking for the Inst's origin. Hence, these objects don't need to even hold a reference to the
// Stackmap.

class StackmapSpecial : public Air::Special {
    WTF_MAKE_TZONE_ALLOCATED_EXPORT(StackmapSpecial, JS_EXPORT_PRIVATE);
public:
    StackmapSpecial();
    ~StackmapSpecial() override;

    enum RoleMode : int8_t {
        SameAsRep,
        ForceLateUseUnlessRecoverable,
        ForceLateUse
    };

protected:
    void reportUsedRegisters(Air::Inst&, const RegisterSetBuilder&) final;
    RegisterSetBuilder extraEarlyClobberedRegs(Air::Inst&) final;
    RegisterSetBuilder extraClobberedRegs(Air::Inst&) final;

    // Note that this does not override generate() or dumpImpl()/deepDumpImpl(). We have many
    // subclasses that implement that.
    void forEachArgImpl(
        unsigned numIgnoredB3Args, unsigned numIgnoredAirArgs,
        Air::Inst&, RoleMode, std::optional<unsigned> firstRecoverableIndex,
        const ScopedLambda<Air::Inst::EachArgCallback>&, std::optional<Width> optionalDefArgWidth);

    bool isValidImpl(
        unsigned numIgnoredB3Args, unsigned numIgnoredAirArgs,
        Air::Inst&);
    bool admitsStackImpl(
        unsigned numIgnoredB3Args, unsigned numIgnoredAirArgs,
        Air::Inst&, unsigned argIndex);

    // Appends the reps for the Inst's args, starting with numIgnoredArgs, to the given vector.
    Vector<ValueRep> repsImpl(
        Air::GenerationContext&, unsigned numIgnoredB3Args, unsigned numIgnoredAirArgs, Air::Inst&);

    static bool isArgValidForType(const Air::Arg&, Type);
    static bool isArgValidForRep(Air::Code&, const Air::Arg&, const ValueRep&);
    static ValueRep repForArg(Air::Code&, const Air::Arg&);
};

} } // namespace JSC::B3

namespace WTF {

void printInternal(PrintStream&, JSC::B3::StackmapSpecial::RoleMode);

} // namespace WTF

#endif // ENABLE(B3_JIT)
