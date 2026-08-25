/*
 * Copyright (C) 2018-2019 Apple Inc. All rights reserved.
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

#include "Options.h"
#include "PropertyOffset.h"
#include "Structure.h"
#include <wtf/CheckedArithmetic.h>
#include <wtf/MathExtras.h>

namespace JSC {

enum class GetByIdMode : uint8_t {
    ProtoLoad = 0, // This must be zero to reuse the higher bits of the pointer as this ProtoLoad mode.
    Default = 1,
    Unset = 2,
    ArrayLength = 3,
    ProtoLoadChain = 4,
};

// Default mode caches up to two own-property hits. The first entry is the most recently recorded
// structure; the second holds the structure it displaced (FIFO), so a site alternating between two
// structures stays on the fast path. The second entry only has 16 bits for its offset, so structures
// whose offset does not fit are simply not kept there.
struct GetByIdModeMetadataDefault {
    StructureID structureID;
    PropertyOffset cachedOffset;
    StructureID secondStructureID;
    int16_t secondCachedOffset;
    // The remaining two bytes hold the mode and hitCountForLLIntCaching of the enclosing union.
    uint8_t padding1;
    uint8_t padding2;
};
static_assert(sizeof(GetByIdModeMetadataDefault) == 16);

struct GetByIdModeMetadataUnset {
    StructureID structureID;
    unsigned padding1;
    unsigned padding2;
};
static_assert(sizeof(GetByIdModeMetadataUnset) == 12);

struct GetByIdModeMetadataArrayLength {
    unsigned padding1;
    unsigned padding2;
    unsigned padding3;
};
static_assert(sizeof(GetByIdModeMetadataArrayLength) == 12);

struct GetByIdModeMetadataProtoLoad {
    StructureID structureID;
    PropertyOffset cachedOffset;
    // Always 64 bits wide, so that the enclosing union has one layout on every target and
    // storing the slot always clears the bytes that overlap mode and hitCountForLLIntCaching.
    uint64_t cachedSlot;
};
static_assert(sizeof(GetByIdModeMetadataProtoLoad) == 16);

// ProtoLoadChain mode caches a prototype hit for up to two receiver structures that reach the same holder
// through the same number of prototype hops. Instead of remembering the holder, the LLInt walks the
// prototype chain starting from the receiver's structure. The watchpoints guarding this cache pin every
// structure on that chain (and a structure's prototype never changes), so the walk always lands on the
// holder. A site starts out in ProtoLoad mode, whose fast path is one load shorter, and only moves here
// once a second receiver structure shows up. Only object receivers can be served by the walk: primitives
// find their prototype through the global object rather than their structure.
struct GetByIdModeMetadataProtoLoadChain {
    StructureID structureID;
    PropertyOffset cachedOffset; // Offset within the holder.
    StructureID secondStructureID;
    uint8_t hopsToHolder; // Number of prototype loads from the receiver to the holder; at least 1.
    // Each time the slow path changes this cache it doubles the number of misses it tolerates before the
    // next change; once that saturates the site is treated as megamorphic and stops rebuilding.
    uint8_t backoffShift;
    // The remaining two bytes hold the mode and hitCountForLLIntCaching of the enclosing union. In this
    // mode the hit count is the number of misses on other structures left before the slow path
    // reconsiders the cache.
    uint8_t padding1;
    uint8_t padding2;

    static constexpr unsigned maxHopsToHolder = std::numeric_limits<uint8_t>::max();
    static constexpr unsigned maxBackoffShift = 7;
};
static_assert(sizeof(GetByIdModeMetadataProtoLoadChain) == 16);

// This union shares ProtoLoad's cachedSlot with "hitCountForLLIntCaching" and "mode".
// This is possible because these values must be zero if we use ProtoLoad mode.
union GetByIdModeMetadata {
    // Multiplier applied to Options::prototypeHitCountForLLIntCaching() when an own-property hit evicts a
    // prototype cache, so that a site mixing the two kinds of hits does not rebuild the prototype cache
    // on every other access.
    static constexpr unsigned prototypeHitCountBackoffAfterOwnHit = 32;

    GetByIdModeMetadata()
    {
        clearToDefaultModeWithoutCache();
    }

    void clearToDefaultModeWithoutCache();
    void setUnsetMode(Structure*);
    void setArrayLengthMode();
    void setProtoLoadMode(Structure*, PropertyOffset, JSObject*);
    void setProtoLoadChainMode(StructureID, StructureID second, PropertyOffset, unsigned hopsToHolder, unsigned backoffShift);

    // The replacement policies: what the slow path records about an own-property hit, and about a
    // prototype hit (hopsToHolder is 0 when the chain walk cannot serve the structure).
    void cacheOwnPropertyLoad(Structure*, PropertyOffset);
    void cachePrototypeLoad(Structure*, PropertyOffset, JSObject* holder, unsigned hopsToHolder);

    bool isPrototypeLoadMode() const { return mode == GetByIdMode::ProtoLoad || mode == GetByIdMode::ProtoLoadChain; }
    bool referencesStructure(StructureID) const;
    // Drops whatever this cache knows about the structure, keeping the other entry if there is one.
    void evictStructure(StructureID);

    struct {
        uint32_t padding1;
        uint32_t padding2;
        uint32_t padding3;
        uint16_t padding4;
        GetByIdMode mode;
        uint8_t hitCountForLLIntCaching; // This must be zero when we use ProtoLoad mode.
    };
    static constexpr ptrdiff_t offsetOfMode() { return OBJECT_OFFSETOF(GetByIdModeMetadata, mode); }
    GetByIdModeMetadataDefault defaultMode;
    GetByIdModeMetadataUnset unsetMode;
    GetByIdModeMetadataArrayLength arrayLengthMode;
    GetByIdModeMetadataProtoLoad protoLoadMode;
    GetByIdModeMetadataProtoLoadChain protoLoadChainMode;

private:
    void clearSecondDefaultEntry();
};
static_assert(sizeof(GetByIdModeMetadata) == 16);

inline void GetByIdModeMetadata::clearSecondDefaultEntry()
{
    defaultMode.secondStructureID = StructureID();
    defaultMode.secondCachedOffset = 0;
}

inline void GetByIdModeMetadata::clearToDefaultModeWithoutCache()
{
    mode = GetByIdMode::Default;
    defaultMode.structureID = StructureID();
    defaultMode.cachedOffset = 0;
    clearSecondDefaultEntry();
    // Whatever invalidated the cache (a watchpoint, GC, or a new kind of hit), the site may still
    // settle on a prototype load later, so let it earn a prototype cache again.
    hitCountForLLIntCaching = clampTo<uint8_t>(Options::prototypeHitCountForLLIntCaching());
}

inline void GetByIdModeMetadata::setUnsetMode(Structure* structure)
{
    clearToDefaultModeWithoutCache();
    mode = GetByIdMode::Unset;
    unsetMode.structureID = structure->id();
}

inline void GetByIdModeMetadata::setArrayLengthMode()
{
    clearToDefaultModeWithoutCache();
    mode = GetByIdMode::ArrayLength;
    // Prevent the prototype cache from ever happening.
    hitCountForLLIntCaching = 0;
}

inline void GetByIdModeMetadata::setProtoLoadMode(Structure* structure, PropertyOffset offset, JSObject* cachedSlot)
{
    // We rely on ProtoLoad being 0, or else the high bits of cachedSlot would write the wrong mode and hit count.
    static_assert(!static_cast<std::underlying_type_t<GetByIdMode>>(GetByIdMode::ProtoLoad));

    protoLoadMode.structureID = structure->id();
    protoLoadMode.cachedOffset = offset;

    // We know that this pointer will remain valid because it will be cleared by either a watchpoint fire or
    // during GC when we clear the LLInt caches.

    // The write to cachedSlot also writes the mode, since they overlap in the struct layout. We know that
    // the mode ProtoLoad is 0 by the static assertion above.
    protoLoadMode.cachedSlot = static_cast<uint64_t>(std::bit_cast<uintptr_t>(cachedSlot));

    ASSERT(mode == GetByIdMode::ProtoLoad);
    ASSERT(!hitCountForLLIntCaching);
    ASSERT(protoLoadMode.structureID == structure->id());
    ASSERT(protoLoadMode.cachedOffset == offset);
    ASSERT(protoLoadMode.cachedSlot == static_cast<uint64_t>(std::bit_cast<uintptr_t>(cachedSlot)));
}

inline void GetByIdModeMetadata::setProtoLoadChainMode(StructureID structureID, StructureID secondStructureID, PropertyOffset offset, unsigned hopsToHolder, unsigned backoffShift)
{
    ASSERT(hopsToHolder >= 1 && hopsToHolder <= GetByIdModeMetadataProtoLoadChain::maxHopsToHolder);
    ASSERT(structureID && structureID != secondStructureID);
    mode = GetByIdMode::ProtoLoadChain;
    protoLoadChainMode.structureID = structureID;
    protoLoadChainMode.cachedOffset = offset;
    protoLoadChainMode.secondStructureID = secondStructureID;
    protoLoadChainMode.hopsToHolder = static_cast<uint8_t>(hopsToHolder);
    protoLoadChainMode.backoffShift = static_cast<uint8_t>(backoffShift);
    // A site that keeps changing its cache is megamorphic; once the backoff saturates, stop rebuilding it.
    hitCountForLLIntCaching = backoffShift < GetByIdModeMetadataProtoLoadChain::maxBackoffShift ? clampTo<uint8_t>(Options::prototypeHitCountForLLIntCaching() << backoffShift) : 0;
}

ALWAYS_INLINE void GetByIdModeMetadata::cacheOwnPropertyLoad(Structure* structure, PropertyOffset offset)
{
    StructureID structureID = structure->id();
    if (mode != GetByIdMode::Default) {
        // An own-property hit evicting a prototype cache means this site mixes the two kinds of hits.
        // Re-arming the prototype cache immediately would make them thrash, so demand more prototype
        // hits than usual before trying again.
        clearToDefaultModeWithoutCache();
        hitCountForLLIntCaching = clampTo<uint8_t>(hitCountForLLIntCaching * prototypeHitCountBackoffAfterOwnHit);
    } else if (defaultMode.structureID == structureID) {
        defaultMode.cachedOffset = offset;
        return;
    } else if (isInBounds<int16_t>(defaultMode.cachedOffset)) {
        // Demote the current first entry to the second one (FIFO). An empty first entry demotes to an
        // empty second entry.
        defaultMode.secondStructureID = defaultMode.structureID;
        defaultMode.secondCachedOffset = static_cast<int16_t>(defaultMode.cachedOffset);
    } else
        clearSecondDefaultEntry();
    defaultMode.structureID = structureID;
    defaultMode.cachedOffset = offset;
}

inline void GetByIdModeMetadata::cachePrototypeLoad(Structure* structure, PropertyOffset offset, JSObject* holder, unsigned hopsToHolder)
{
    StructureID structureID = structure->id();
    if (mode == GetByIdMode::ProtoLoadChain) {
        ASSERT(hopsToHolder);
        auto& chain = protoLoadChainMode;
        if (chain.structureID == structureID || chain.secondStructureID == structureID)
            return;
        // Same chain shape: the current first entry becomes the second one (FIFO). Otherwise start over
        // with this structure alone. Either way the site tolerates twice as many misses before the next change.
        bool compatible = chain.cachedOffset == offset && chain.hopsToHolder == hopsToHolder;
        setProtoLoadChainMode(structureID, compatible ? chain.structureID : StructureID(), offset, hopsToHolder, chain.backoffShift + 1);
        return;
    }
    setProtoLoadMode(structure, offset, holder);
}

inline bool GetByIdModeMetadata::referencesStructure(StructureID structureID) const
{
    switch (mode) {
    case GetByIdMode::Default:
        return defaultMode.structureID == structureID || defaultMode.secondStructureID == structureID;
    case GetByIdMode::Unset:
        return unsetMode.structureID == structureID;
    case GetByIdMode::ProtoLoad:
        return protoLoadMode.structureID == structureID;
    case GetByIdMode::ProtoLoadChain:
        return protoLoadChainMode.structureID == structureID || protoLoadChainMode.secondStructureID == structureID;
    case GetByIdMode::ArrayLength:
        return false;
    }
    RELEASE_ASSERT_NOT_REACHED();
    return false;
}

inline void GetByIdModeMetadata::evictStructure(StructureID structureID)
{
    switch (mode) {
    case GetByIdMode::Default:
        if (defaultMode.secondStructureID == structureID)
            clearSecondDefaultEntry();
        if (defaultMode.structureID != structureID)
            return;
        if (!defaultMode.secondStructureID)
            break;
        defaultMode.structureID = defaultMode.secondStructureID;
        defaultMode.cachedOffset = defaultMode.secondCachedOffset;
        clearSecondDefaultEntry();
        return;
    case GetByIdMode::ProtoLoadChain:
        if (protoLoadChainMode.secondStructureID == structureID)
            protoLoadChainMode.secondStructureID = StructureID();
        if (protoLoadChainMode.structureID != structureID)
            return;
        if (!protoLoadChainMode.secondStructureID)
            break;
        protoLoadChainMode.structureID = protoLoadChainMode.secondStructureID;
        protoLoadChainMode.secondStructureID = StructureID();
        return;
    default:
        if (!referencesStructure(structureID))
            return;
        break;
    }
    clearToDefaultModeWithoutCache();
}

} // namespace JSC
