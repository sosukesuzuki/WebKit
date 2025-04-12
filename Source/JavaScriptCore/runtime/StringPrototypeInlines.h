/*
 * Copyright (C) 2019-2024 Apple, Inc. All rights reserved.
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

#include "CachedCall.h"
#include "ExceptionHelpers.h"
#include "JSImmutableButterfly.h"
#include "ObjectConstructor.h"
#include "ParseInt.h"
#include "StringPrototype.h"
#include "StringReplaceCacheInlines.h"
#include "RegExpGlobalData.h"
#include "RegExpGlobalDataInlines.h"
#include "RegExpObject.h"
#include <wtf/Range.h>
#include <wtf/text/MakeString.h>
#include <wtf/text/StringSearch.h>

WTF_ALLOW_UNSAFE_BUFFER_USAGE_BEGIN

namespace JSC {

inline Structure* StringPrototype::createStructure(VM& vm, JSGlobalObject* globalObject, JSValue prototype)
{
    return Structure::create(vm, globalObject, prototype, TypeInfo(DerivedStringObjectType, StructureFlags), info());
}

ALWAYS_INLINE std::tuple<int32_t, int32_t> extractSliceOffsets(int32_t length, int32_t startValue, std::optional<int32_t> endValue)
{
    int32_t from;
    if (startValue < 0)
        from = std::max<int32_t>(length + startValue, 0);
    else
        from = std::min<int32_t>(startValue, length);

    int32_t end = endValue.value_or(length);
    int32_t to;
    if (end < 0)
        to = std::max<int32_t>(length + end, 0);
    else
        to = std::min<int32_t>(end, length);

    if (from >= to)
        return { 0, 0 };
    return { from, to };
}

template<typename NumberType>
ALWAYS_INLINE JSString* stringSlice(JSGlobalObject* globalObject, VM& vm, JSString* string, int32_t length, NumberType start, std::optional<NumberType> endValue)
{
    if constexpr (std::is_same_v<NumberType, int32_t>) {
        auto [from, to] = extractSliceOffsets(length, start, endValue);
        return jsSubstring(vm, globalObject, string, from, to - from);
    } else {
        NumberType from = start < 0 ? length + start : start;
        NumberType end = endValue.value_or(length);
        NumberType to = end < 0 ? length + end : end;
        if (to > from && to > 0 && from < length) {
            if (from < 0)
                from = 0;
            if (to > length)
                to = length;
            return jsSubstring(vm, globalObject, string, static_cast<unsigned>(from), static_cast<unsigned>(to) - static_cast<unsigned>(from));
        }
        return jsEmptyString(vm);
    }
}

ALWAYS_INLINE std::tuple<int32_t, int32_t> extractSubstringOffsets(int32_t length, int32_t startValue, std::optional<int32_t> endValue)
{
    int32_t start = std::min<int32_t>(std::max<int32_t>(startValue, 0), length);
    int32_t end = length;
    if (endValue)
        end = std::min<int32_t>(std::max<int32_t>(endValue.value(), 0), length);

    ASSERT(start >= 0);
    ASSERT(end >= 0);
    if (start > end)
        std::swap(start, end);
    return { start, end };
}

ALWAYS_INLINE JSString* stringSubstring(JSGlobalObject* globalObject, JSString* string, int32_t startValue, std::optional<int32_t> endValue)
{
    int length = string->length();
    RELEASE_ASSERT(length >= 0);

    auto [start, end] = extractSubstringOffsets(length, startValue, endValue);

    return jsSubstring(globalObject, string, start, end - start);
}

ALWAYS_INLINE JSString* jsSpliceSubstringsWithSeparators(JSGlobalObject* globalObject, JSString* sourceVal, const String& source, const Range<int32_t>* substringRanges, int rangeCount, const String* separators, int separatorCount)
{
    VM& vm = getVM(globalObject);
    auto scope = DECLARE_THROW_SCOPE(vm);

    if (rangeCount == 1 && separatorCount == 0) {
        int sourceSize = source.length();
        int position = substringRanges[0].begin();
        int length = substringRanges[0].distance();
        if (position <= 0 && length >= sourceSize)
            return sourceVal;
        // We could call String::substringSharingImpl(), but this would result in redundant checks.
        RELEASE_AND_RETURN(scope, jsString(vm, StringImpl::createSubstringSharingImpl(*source.impl(), std::max(0, position), std::min(sourceSize, length))));
    }

    if (rangeCount == 2 && separatorCount == 1) {
        String leftPart(StringImpl::createSubstringSharingImpl(*source.impl(), substringRanges[0].begin(), substringRanges[0].distance()));
        String rightPart(StringImpl::createSubstringSharingImpl(*source.impl(), substringRanges[1].begin(), substringRanges[1].distance()));
        RELEASE_AND_RETURN(scope, jsString(globalObject, leftPart, separators[0], rightPart));
    }

    CheckedInt32 totalLength = 0;
    bool allSeparators8Bit = true;
    for (int i = 0; i < rangeCount; i++)
        totalLength += substringRanges[i].distance();
    for (int i = 0; i < separatorCount; i++) {
        totalLength += separators[i].length();
        if (separators[i].length() && !separators[i].is8Bit())
            allSeparators8Bit = false;
    }
    if (totalLength.hasOverflowed()) {
        throwOutOfMemoryError(globalObject, scope);
        return nullptr;
    }

    if (!totalLength)
        return jsEmptyString(vm);

    if (source.is8Bit() && allSeparators8Bit) {
        std::span<LChar> buffer;
        auto impl = StringImpl::tryCreateUninitialized(totalLength, buffer);
        if (!impl) {
            throwOutOfMemoryError(globalObject, scope);
            return nullptr;
        }

        int maxCount = std::max(rangeCount, separatorCount);
        Checked<int, AssertNoOverflow> bufferPos = 0;
        for (int i = 0; i < maxCount; i++) {
            if (i < rangeCount) {
                auto substring = StringView { source }.substring(substringRanges[i].begin(), substringRanges[i].distance());
                substring.getCharacters8(buffer.subspan(bufferPos.value()));
                bufferPos += substring.length();
            }
            if (i < separatorCount) {
                StringView separator = separators[i];
                separator.getCharacters8(buffer.subspan(bufferPos.value()));
                bufferPos += separator.length();
            }
        }

        RELEASE_AND_RETURN(scope, jsString(vm, impl.releaseNonNull()));
    }

    std::span<UChar> buffer;
    auto impl = StringImpl::tryCreateUninitialized(totalLength, buffer);
    if (!impl) {
        throwOutOfMemoryError(globalObject, scope);
        return nullptr;
    }

    int maxCount = std::max(rangeCount, separatorCount);
    Checked<int, AssertNoOverflow> bufferPos = 0;
    for (int i = 0; i < maxCount; i++) {
        if (i < rangeCount) {
            auto substring = StringView { source }.substring(substringRanges[i].begin(), substringRanges[i].distance());
            substring.getCharacters(buffer.subspan(bufferPos.value()));
            bufferPos += substring.length();
        }
        if (i < separatorCount) {
            StringView separator = separators[i];
            separator.getCharacters(buffer.subspan(bufferPos.value()));
            bufferPos += separator.length();
        }
    }

    RELEASE_AND_RETURN(scope, jsString(vm, impl.releaseNonNull()));
}

enum class StringReplaceSubstitutions : bool { No, Yes };

template<StringReplaceSubstitutions substitutions>
ALWAYS_INLINE String tryMakeReplacedString(const String& string, const String& replacement, size_t matchStart, size_t matchEnd)
{
    if constexpr (substitutions == StringReplaceSubstitutions::Yes) {
        size_t dollarPos = replacement.find('$');
        if (dollarPos != WTF::notFound) {
            StringBuilder builder(OverflowPolicy::RecordOverflow);
            int ovector[2] = { static_cast<int>(matchStart), static_cast<int>(matchEnd) };
            substituteBackreferencesSlow(builder, replacement, string, ovector, nullptr, dollarPos);
            if (UNLIKELY(builder.hasOverflowed()))
                return { };
            if (auto result = tryMakeString(StringView(string).substring(0, matchStart), builder.toString(), StringView(string).substring(matchEnd, string.length() - matchEnd)); LIKELY(!result.isNull()))
                return result;
        }
    }
    return tryMakeString(StringView(string).substring(0, matchStart), replacement, StringView(string).substring(matchEnd, string.length() - matchEnd));
}

template<StringReplaceSubstitutions substitutions>
ALWAYS_INLINE String tryMakeReplacedAllString(const String& string, const String& replacement, const Vector<size_t, 16>& matchStarts, size_t searchLength)
{
    auto resultLength = CheckedSize { string.length() + matchStarts.size() * (replacement.length() - searchLength) };

    StringBuilder resultBuilder(OverflowPolicy::RecordOverflow);
    resultBuilder.reserveCapacity(resultLength);

    size_t lastMatchEnd = 0;
    for (auto start : matchStarts) {
        resultBuilder.append(StringView(string).substring(lastMatchEnd, start - lastMatchEnd));
        if constexpr (substitutions == StringReplaceSubstitutions::Yes) {
            int ovector[2] = { static_cast<int>(start), static_cast<int>(start + searchLength) };
            substituteBackreferences(resultBuilder, replacement, string, ovector, nullptr);
        } else
            resultBuilder.append(replacement);
        lastMatchEnd = start + searchLength;
    }
    resultBuilder.append(StringView(string).substring(lastMatchEnd));

    if (UNLIKELY(resultBuilder.hasOverflowed()))
        return { };

    return resultBuilder.toString();
}

enum class StringReplaceUseTable : bool { No, Yes };
template<StringReplaceSubstitutions substitutions, StringReplaceUseTable useTable, typename TableType>
ALWAYS_INLINE JSString* stringReplaceStringString(JSGlobalObject* globalObject, JSString* stringCell, const String& string, const String& search, const String& replacement, const TableType* table)
{
    VM& vm = globalObject->vm();
    auto scope = DECLARE_THROW_SCOPE(vm);

    size_t matchStart;
    if constexpr (useTable == StringReplaceUseTable::Yes)
        matchStart = table->find(string, search);
    else {
        UNUSED_PARAM(table);
        matchStart = StringView(string).find(vm.adaptiveStringSearcherTables(), StringView(search));
    }
    if (matchStart == notFound)
        return stringCell;

    size_t searchLength = search.length();
    size_t matchEnd = matchStart + searchLength;
    auto result = tryMakeReplacedString<substitutions>(string, replacement, matchStart, matchEnd);
    if (UNLIKELY(!result)) {
        throwOutOfMemoryError(globalObject, scope);
        return nullptr;
    }

    return jsString(vm, WTFMove(result));
}

template<StringReplaceSubstitutions substitutions, StringReplaceUseTable useTable, typename TableType>
ALWAYS_INLINE JSString* stringReplaceAllStringString(JSGlobalObject* globalObject, JSString* stringCell, const String& string, const String& search, const String& replacement, const TableType* table)
{
    VM& vm = globalObject->vm();
    auto scope = DECLARE_THROW_SCOPE(vm);

    Vector<size_t, 16> matchStarts;
    size_t searchLength = search.length();

    size_t matchStart = 0;
    while (true) {
        size_t found;

        if constexpr (useTable == StringReplaceUseTable::Yes) {
            size_t foundRelative = table->find(StringView(string).substring(matchStart), search);
            if (foundRelative == notFound)
                found = notFound;
            else
                found = matchStart + foundRelative;
        } else
            found = StringView(string).find(vm.adaptiveStringSearcherTables(), StringView(search), matchStart);

        if (found == notFound)
            break;

        matchStarts.append(found);
        matchStart = found + searchLength;
        if (search.isEmpty())
            ++matchStart;
    }

    if (matchStarts.isEmpty())
        return stringCell;

    auto replacedString = tryMakeReplacedAllString<substitutions>(string, replacement, matchStarts, searchLength);
    if (UNLIKELY(!replacedString)) {
        throwOutOfMemoryError(globalObject, scope);
        return nullptr;
    }

    return jsString(vm, replacedString);
}

enum class StringReplaceMode : bool { Single, Global };
inline JSString* replaceUsingStringSearch(VM& vm, JSGlobalObject* globalObject, JSString* jsString, const String& string, const String& searchString, JSValue replaceValue, StringReplaceMode mode)
{
    auto scope = DECLARE_THROW_SCOPE(vm);

    CallData callData;
    std::optional<CachedCall> cachedCall;
    String replaceString;
    if (replaceValue.isString()) {
        replaceString = asString(replaceValue)->value(globalObject);
        RETURN_IF_EXCEPTION(scope, nullptr);
    } else {
        callData = JSC::getCallData(replaceValue);
        if (callData.type == CallData::Type::None) {
            replaceString = replaceValue.toWTFString(globalObject);
            RETURN_IF_EXCEPTION(scope, nullptr);
        } else if (callData.type == CallData::Type::JS) {
            cachedCall.emplace(globalObject, jsCast<JSFunction*>(replaceValue), 3);
            RETURN_IF_EXCEPTION(scope, nullptr);
        }
    }

    if (!replaceString.isNull()) {
        if (mode == StringReplaceMode::Single)
            RELEASE_AND_RETURN(scope, (stringReplaceStringString<StringReplaceSubstitutions::Yes, StringReplaceUseTable::No, BoyerMooreHorspoolTable<uint8_t>>(globalObject, jsString, string, searchString, replaceString, nullptr)));
        else {
            ASSERT(mode == StringReplaceMode::Global);
            RELEASE_AND_RETURN(scope, (stringReplaceAllStringString<StringReplaceSubstitutions::Yes, StringReplaceUseTable::No, BoyerMooreHorspoolTable<uint8_t>>(globalObject, jsString, string, searchString, replaceString, nullptr)));
        }
    }

    ASSERT(callData.type != CallData::Type::None);

    size_t matchStart = StringView(string).find(vm.adaptiveStringSearcherTables(), StringView(searchString));
    if (matchStart == notFound)
        return jsString;

    size_t endOfLastMatch = 0;
    size_t searchStringLength = searchString.length();
    Vector<Range<int32_t>, 16> sourceRanges;
    Vector<String, 16> replacements;
    do {
        JSValue replacement;
        if (cachedCall) {
            auto* substring = jsSubstring(vm, globalObject, jsString, matchStart, searchStringLength);
            RETURN_IF_EXCEPTION(scope, nullptr);
            replacement = cachedCall->callWithArguments(globalObject, jsUndefined(), substring, jsNumber(matchStart), jsString);
            RETURN_IF_EXCEPTION(scope, nullptr);
        } else {
            MarkedArgumentBuffer args;
            auto* substring = jsSubstring(vm, globalObject, jsString, matchStart, searchString.impl()->length());
            RETURN_IF_EXCEPTION(scope, nullptr);
            args.append(substring);
            args.append(jsNumber(matchStart));
            args.append(jsString);
            ASSERT(!args.hasOverflowed());
            replacement = call(globalObject, replaceValue, callData, jsUndefined(), args);
            RETURN_IF_EXCEPTION(scope, nullptr);
        }
        replaceString = replacement.toWTFString(globalObject);
        RETURN_IF_EXCEPTION(scope, nullptr);

        if (UNLIKELY(!sourceRanges.tryConstructAndAppend(endOfLastMatch, matchStart))) {
            throwOutOfMemoryError(globalObject, scope);
            return nullptr;
        }

        size_t matchEnd = matchStart + searchStringLength;
        replacements.append(replaceString);

        endOfLastMatch = matchEnd;
        if (mode == StringReplaceMode::Single)
            break;
        matchStart = StringView(string).find(vm.adaptiveStringSearcherTables(), StringView(searchString), !searchStringLength ? endOfLastMatch + 1 : endOfLastMatch);
    } while (matchStart != notFound);

    if (UNLIKELY(!sourceRanges.tryConstructAndAppend(endOfLastMatch, string.length()))) {
        throwOutOfMemoryError(globalObject, scope);
        return nullptr;
    }
    RELEASE_AND_RETURN(scope, jsSpliceSubstringsWithSeparators(globalObject, jsString, string, sourceRanges.data(), sourceRanges.size(), replacements.data(), replacements.size()));
}

enum class DollarCheck : uint8_t { Yes, No };
template<DollarCheck check = DollarCheck::Yes>
inline JSString* tryReplaceOneCharUsingString(JSGlobalObject* globalObject, JSString* string, JSString* search, JSString* replacement)
{
    VM& vm = globalObject->vm();
    auto scope = DECLARE_THROW_SCOPE(vm);

    // FIXME: Substring should be supported. However, substring of substring is not allowed at the moment.
    if (!string->isNonSubstringRope() || string->length() < 0x128)
        return nullptr;

    RETURN_IF_EXCEPTION(scope, nullptr);
    auto searchString = search->value(globalObject);
    if (searchString->length() != 1)
        return nullptr;

    auto replaceString = replacement->value(globalObject);
    RETURN_IF_EXCEPTION(scope, nullptr);
    if constexpr (check == DollarCheck::Yes) {
        if (replaceString->find('$') != notFound)
            return nullptr;
    }

    RELEASE_AND_RETURN(scope, string->tryReplaceOneChar(globalObject, searchString[0], replacement));
}

static ALWAYS_INLINE JSString* jsSpliceSubstrings(JSGlobalObject* globalObject, JSString* sourceVal, const String& source, std::span<const Range<int32_t>> substringRanges)
{
    VM& vm = globalObject->vm();
    auto scope = DECLARE_THROW_SCOPE(vm);

    if (substringRanges.size() == 1) {
        int sourceSize = source.length();
        int position = substringRanges.front().begin();
        int length = substringRanges.front().distance();
        if (position <= 0 && length >= sourceSize)
            return sourceVal;
        // We could call String::substringSharingImpl(), but this would result in redundant checks.
        RELEASE_AND_RETURN(scope, jsString(vm, StringImpl::createSubstringSharingImpl(*source.impl(), std::max(0, position), std::min(sourceSize, length))));
    }

    // We know that the sum of substringRanges lengths cannot exceed length of
    // source because the substringRanges were computed from the source string
    // in removeUsingRegExpSearch(). Hence, totalLength cannot exceed
    // String::MaxLength, and therefore, cannot overflow.
    Checked<int, AssertNoOverflow> totalLength = 0;
    for (auto& range : substringRanges)
        totalLength += range.distance();
    ASSERT(totalLength <= static_cast<int>(String::MaxLength));

    if (!totalLength)
        return jsEmptyString(vm);

    if (source.is8Bit()) {
        std::span<LChar> buffer;
        auto sourceData = source.span8();
        auto impl = StringImpl::tryCreateUninitialized(totalLength, buffer);
        if (!impl) {
            throwOutOfMemoryError(globalObject, scope);
            return nullptr;
        }

        Checked<size_t, AssertNoOverflow> bufferPos = 0;
        for (auto range : substringRanges) {
            size_t srcLen = range.distance();
            StringImpl::copyCharacters(buffer.subspan(bufferPos.value()), sourceData.subspan(range.begin(), srcLen));
            bufferPos += srcLen;
        }

        RELEASE_AND_RETURN(scope, jsString(vm, impl.releaseNonNull()));
    }

    std::span<UChar> buffer;
    auto sourceData = source.span16();

    auto impl = StringImpl::tryCreateUninitialized(totalLength, buffer);
    if (!impl) {
        throwOutOfMemoryError(globalObject, scope);
        return nullptr;
    }

    Checked<size_t, AssertNoOverflow> bufferPos = 0;
    for (auto& range : substringRanges) {
        size_t srcLen = range.distance();
        StringImpl::copyCharacters(buffer.subspan(bufferPos.value()), sourceData.subspan(range.begin(), srcLen));
        bufferPos += srcLen;
    }

    RELEASE_AND_RETURN(scope, jsString(vm, impl.releaseNonNull()));
}

#define OUT_OF_MEMORY(exec__, scope__) \
    do { \
        throwOutOfMemoryError(exec__, scope__); \
        return nullptr; \
    } while (false)

static ALWAYS_INLINE JSString* removeUsingRegExpSearch(VM& vm, JSGlobalObject* globalObject, JSString* string, const String& source, RegExp* regExp)
{
    auto scope = DECLARE_THROW_SCOPE(vm);
    SuperSamplerScope superSamplerScope(false);

    size_t lastIndex = 0;
    unsigned startPosition = 0;
    Vector<Range<int32_t>, 64> sourceRanges;
    unsigned sourceLen = source.length();

    auto genericMatches = [&](VM& vm, auto input, auto pattern) ALWAYS_INLINE_LAMBDA -> size_t {
        ASSERT(!pattern.empty());
        unsigned startIndex = 0;
        if (pattern.size() == 1) {
            size_t lastFound = notFound;
            auto patternCharacter = pattern[0];
            for (size_t i = 0; i < input.size(); ++i) {
                if (input[i] != patternCharacter)
                    continue;
                if (startIndex < i) {
                    if (UNLIKELY(!sourceRanges.tryConstructAndAppend(startIndex, i))) {
                        throwOutOfMemoryError(globalObject, scope);
                        return notFound;
                    }
                }
                lastFound = i;
                startIndex = i + 1;
            }
            if (lastFound == notFound)
                return lastFound;

            if (startIndex < sourceLen) {
                if (UNLIKELY(!sourceRanges.tryConstructAndAppend(startIndex, sourceLen))) {
                    throwOutOfMemoryError(globalObject, scope);
                    return notFound;
                }
            }
            return lastFound;
        }

        AdaptiveStringSearcher<typename decltype(pattern)::value_type, typename decltype(input)::value_type> search(vm.adaptiveStringSearcherTables(), pattern);
        size_t found = search.search(input, startIndex);
        if (found == notFound)
            return notFound;

        size_t lastFound = notFound;
        do {
            if (startIndex < found) {
                if (UNLIKELY(!sourceRanges.tryConstructAndAppend(startIndex, found))) {
                    throwOutOfMemoryError(globalObject, scope);
                    return notFound;
                }
            }
            startIndex = found + pattern.size();
            lastFound = found;
            found = search.search(input, startIndex);
        } while (found != notFound);

        if (startIndex < sourceLen) {
            if (UNLIKELY(!sourceRanges.tryConstructAndAppend(startIndex, sourceLen))) {
                throwOutOfMemoryError(globalObject, scope);
                return notFound;
            }
        }
        return lastFound;
    };

    if (regExp->hasValidAtom()) {
        const String& pattern = regExp->atom();
        ASSERT(!pattern.isEmpty());
        size_t lastIndex = 0;
        if (pattern.is8Bit()) {
            if (source.is8Bit())
                lastIndex = genericMatches(vm, source.span8(), pattern.span8());
            else
                lastIndex = genericMatches(vm, source.span16(), pattern.span8());
        } else {
            if (source.is8Bit())
                lastIndex = genericMatches(vm, source.span8(), pattern.span16());
            else
                lastIndex = genericMatches(vm, source.span16(), pattern.span16());
        }
        RETURN_IF_EXCEPTION(scope, nullptr);
        if (lastIndex == notFound)
            return string;

        // Record the last matching.
        globalObject->regExpGlobalData().recordMatch(vm, globalObject, regExp, string, MatchResult { static_cast<unsigned>(lastIndex), static_cast<unsigned>(lastIndex + pattern.length()) }, /* oneCharacterMatch */ false);
        RELEASE_AND_RETURN(scope, jsSpliceSubstrings(globalObject, string, source, sourceRanges.span()));
    }

    while (true) {
        MatchResult result = globalObject->regExpGlobalData().performMatch(globalObject, regExp, string, source, startPosition);
        RETURN_IF_EXCEPTION(scope, nullptr);
        if (!result)
            break;

        if (lastIndex < result.start) {
            if (UNLIKELY(!sourceRanges.tryConstructAndAppend(lastIndex, result.start)))
                OUT_OF_MEMORY(globalObject, scope);
        }
        lastIndex = result.end;
        startPosition = lastIndex;

        // special case of empty match
        if (result.empty()) {
            startPosition++;
            if (startPosition > sourceLen)
                break;
        }
    }

    if (!lastIndex)
        return string;

    if (static_cast<unsigned>(lastIndex) < sourceLen) {
        if (UNLIKELY(!sourceRanges.tryConstructAndAppend(lastIndex, sourceLen)))
            OUT_OF_MEMORY(globalObject, scope);
    }
    RELEASE_AND_RETURN(scope, jsSpliceSubstrings(globalObject, string, source, sourceRanges.span()));
}

static ALWAYS_INLINE JSString* replaceUsingRegExpSearchWithCache(VM& vm, JSGlobalObject* globalObject, JSString* string, const String& source, RegExp* regExp, JSFunction* replaceFunction)
{
    auto scope = DECLARE_THROW_SCOPE(vm);
    SuperSamplerScope superSamplerScope(true);

    ASSERT(!string->isRope()); // This is already resolved.
    ASSERT(source.length() >= Options::thresholdForStringReplaceCache());
    // Currently not caching results when named captures are specified.
    ASSERT(!regExp->hasNamedCaptures());

    unsigned sourceLen = source.length();
    unsigned cachedCount = regExp->numSubpatterns() + 2;
    unsigned argCount = cachedCount + 1;

    JSImmutableButterfly* result = nullptr;

    auto* entry = vm.stringReplaceCache.get(source, regExp);
    if (!entry) {
        // This is either a loop (if global is set) or a one-way (if not).
        // regExp->numSubpatterns() + 1 for pattern args, + 2 for match start and string
        size_t lastIndex = 0;
        unsigned startPosition = 0;
        MarkedArgumentBuffer results;
        while (true) {
            int* ovector;
            MatchResult result = globalObject->regExpGlobalData().performMatch(globalObject, regExp, string, source, startPosition, &ovector);
            RETURN_IF_EXCEPTION(scope, nullptr);
            if (!result)
                break;

            for (unsigned i = 0; i < regExp->numSubpatterns() + 1; ++i) {
                int matchStart = ovector[i * 2];
                int matchLen = ovector[i * 2 + 1] - matchStart;

                JSValue patternValue;

                if (matchStart < 0)
                    patternValue = jsUndefined();
                else {
                    patternValue = jsSubstringOfResolved(vm, string, matchStart, matchLen);
                    RETURN_IF_EXCEPTION(scope, { });
                }

                results.append(patternValue);
            }

            results.append(jsNumber(result.start));

            lastIndex = result.end;
            startPosition = lastIndex;

            // special case of empty match
            if (result.empty()) {
                startPosition++;
                if (startPosition > sourceLen)
                    break;
                if (U16_IS_LEAD(source[startPosition - 1]) && U16_IS_TRAIL(source[startPosition])) {
                    startPosition++;
                    if (startPosition > sourceLen)
                        break;
                }
            }
        }

        // Nothing matches.
        if (results.isEmpty())
            return string;

        result = JSImmutableButterfly::tryCreateFromArgList(vm, results);
        if (UNLIKELY(!result)) {
            throwOutOfMemoryError(globalObject, scope);
            return nullptr;
        }

        vm.stringReplaceCache.set(source, regExp, result, globalObject->regExpGlobalData().matchResult(), globalObject->regExpGlobalData().ovector());
    } else {
        result = entry->m_result;
        auto lastMatch = entry->m_lastMatch;
        auto matchResult = entry->m_matchResult;
        globalObject->regExpGlobalData().resetResultFromCache(globalObject, regExp, string, matchResult, WTFMove(lastMatch));
    }

    // regExp->numSubpatterns() + 1 for pattern args, + 2 for match start and string
    unsigned length = result->length();
    unsigned items = length / cachedCount;
    Vector<String, 16> replacements;

    if (UNLIKELY(!replacements.tryReserveCapacity(items))) {
        throwOutOfMemoryError(globalObject, scope);
        return nullptr;
    }
    replacements.grow(items);

    CachedCall cachedCall(globalObject, replaceFunction, argCount);
    RETURN_IF_EXCEPTION(scope, nullptr);
    if (argCount == 3) {
        ASSERT(!regExp->numSubpatterns());
        ASSERT(cachedCount == 2);
        uint64_t totalLength = 0;
        bool replacementsAre8Bit = true;
        {
            size_t lastIndex = 0;
            size_t index = 0;
            for (auto& slot : replacements) {
                JSString* matchedString = asString(result->get(index * 2));
                JSValue startOffset = result->get(index * 2 + 1);

                int32_t start = startOffset.asInt32();
                int32_t end = start + matchedString->length();

                JSValue jsResult = cachedCall.callWithArguments(globalObject, jsUndefined(), matchedString, startOffset, string);
                RETURN_IF_EXCEPTION_WITH_TRAPS_DEFERRED(scope, nullptr);

                auto string = jsResult.toWTFString(globalObject);
                RETURN_IF_EXCEPTION_WITH_TRAPS_DEFERRED(scope, nullptr);

                replacementsAre8Bit &= string.is8Bit();
                totalLength += string.length();
                totalLength += (start - lastIndex);
                slot = WTFMove(string);

                lastIndex = end;
                ++index;
            }
            if (static_cast<unsigned>(lastIndex) < sourceLen)
                totalLength += (sourceLen - lastIndex);
        }

        if (UNLIKELY(totalLength > StringImpl::MaxLength)) {
            throwOutOfMemoryError(globalObject, scope);
            return nullptr;
        }

        StringView sourceView { source };
        if (sourceView.is8Bit() && replacementsAre8Bit) {
            std::span<LChar> buffer;
            auto impl = StringImpl::tryCreateUninitialized(totalLength, buffer);
            if (UNLIKELY(!impl)) {
                throwOutOfMemoryError(globalObject, scope);
                return nullptr;
            }

            size_t lastIndex = 0;
            unsigned index = 0;
            size_t bufferPos = 0;
            for (auto& replacement : replacements) {
                int32_t length = asString(result->get(index * 2))->length();
                int32_t start = result->get(index * 2 + 1).asInt32();
                int32_t end = start + length;

                auto substring = sourceView.substring(lastIndex, start - lastIndex);
                substring.getCharacters8(buffer.subspan(bufferPos));
                bufferPos += substring.length();

                StringView { replacement }.getCharacters8(buffer.subspan(bufferPos));
                bufferPos += replacement.length();

                ++index;
                lastIndex = end;
            }
            if (static_cast<unsigned>(lastIndex) < sourceLen) {
                auto substring = sourceView.substring(lastIndex, sourceLen - lastIndex);
                substring.getCharacters8(buffer.subspan(bufferPos));
            }

            ASSERT(lastIndex <= sourceLen && (bufferPos + (sourceLen - lastIndex)) == totalLength);
            RELEASE_AND_RETURN(scope, jsString(vm, impl.releaseNonNull()));
        }

        std::span<UChar> buffer;
        auto impl = StringImpl::tryCreateUninitialized(totalLength, buffer);
        if (UNLIKELY(!impl)) {
            throwOutOfMemoryError(globalObject, scope);
            return nullptr;
        }

        size_t lastIndex = 0;
        unsigned index = 0;
        size_t bufferPos = 0;
        for (auto& replacement : replacements) {
            int32_t length = asString(result->get(index * 2))->length();
            int32_t start = result->get(index * 2 + 1).asInt32();
            int32_t end = start + length;

            auto substring = sourceView.substring(lastIndex, start - lastIndex);
            substring.getCharacters(buffer.subspan(bufferPos));
            bufferPos += substring.length();

            StringView { replacement }.getCharacters(buffer.subspan(bufferPos));
            bufferPos += replacement.length();

            ++index;
            lastIndex = end;
        }
        if (static_cast<unsigned>(lastIndex) < sourceLen) {
            auto substring = sourceView.substring(lastIndex, sourceLen - lastIndex);
            substring.getCharacters(buffer.subspan(bufferPos));
        }

        ASSERT(lastIndex <= sourceLen && (bufferPos + (sourceLen - lastIndex)) == totalLength);
        RELEASE_AND_RETURN(scope, jsString(vm, impl.releaseNonNull()));
    }

    Vector<Range<int32_t>, 16> sourceRanges;
    if (UNLIKELY(!sourceRanges.tryReserveCapacity(items + 1))) {
        throwOutOfMemoryError(globalObject, scope);
        return nullptr;
    }

    size_t lastIndex = 0;
    size_t cursor = 0;
    for (auto& slot : replacements) {
        cachedCall.clearArguments();
        for (unsigned i = 0; i < cachedCount; ++i)
            cachedCall.appendArgument(result->get(cursor + i));
        cachedCall.appendArgument(string);

        int32_t start = result->get(cursor + cachedCount - 1).asInt32();
        int32_t end = start + asString(result->get(cursor))->length();

        sourceRanges.constructAndAppend(lastIndex, start);

        cachedCall.setThis(jsUndefined());
        if (UNLIKELY(cachedCall.hasOverflowedArguments())) {
            throwOutOfMemoryError(globalObject, scope);
            return nullptr;
        }

        JSValue jsResult = cachedCall.call();
        RETURN_IF_EXCEPTION_WITH_TRAPS_DEFERRED(scope, nullptr);

        auto string = jsResult.toWTFString(globalObject);
        RETURN_IF_EXCEPTION_WITH_TRAPS_DEFERRED(scope, nullptr);

        slot = WTFMove(string);

        lastIndex = end;
        cursor += cachedCount;
    }

    if (static_cast<unsigned>(lastIndex) < sourceLen)
        sourceRanges.constructAndAppend(lastIndex, sourceLen);
    RELEASE_AND_RETURN(scope, jsSpliceSubstringsWithSeparators(globalObject, string, source, sourceRanges.data(), sourceRanges.size(), replacements.data(), replacements.size()));
}

static ALWAYS_INLINE JSString* tryTrimSpaces(VM& vm, JSGlobalObject* globalObject, const String& source, JSString* string, RegExp* regExp)
{
    unsigned sourceLen = source.length();
    unsigned left = 0;
    unsigned right = sourceLen;
    switch (regExp->specificPattern()) {
    case Yarr::SpecificPattern::TrailingSpacesPlus: {
        while (right > 0 && isStrWhiteSpace(source[right - 1]))
            right--;

        if (right == sourceLen) {
            // Not found.
            return string;
        }

        if (!right) {
            // Everything is spaces.
            globalObject->regExpGlobalData().resetResultFromCache(globalObject, regExp, string, MatchResult { 0, sourceLen }, { });
            return jsEmptyString(vm);
        }

        globalObject->regExpGlobalData().resetResultFromCache(globalObject, regExp, string, MatchResult { right, sourceLen }, { });
        return jsString(vm, source.substringSharingImpl(0, right));
    }
    case Yarr::SpecificPattern::LeadingSpacesPlus: {
        while (left < sourceLen && isStrWhiteSpace(source[left]))
            left++;

        if (!left)
            return string;

        if (left == sourceLen) {
            // Everything is spaces.
            globalObject->regExpGlobalData().resetResultFromCache(globalObject, regExp, string, MatchResult { 0, sourceLen }, { });
            return jsEmptyString(vm);
        }

        globalObject->regExpGlobalData().resetResultFromCache(globalObject, regExp, string, MatchResult { 0, left }, { });
        return jsString(vm, source.substringSharingImpl(left, sourceLen));
    }
    case Yarr::SpecificPattern::TrailingSpacesStar:
    case Yarr::SpecificPattern::LeadingSpacesStar:
    case Yarr::SpecificPattern::Atom:
    case Yarr::SpecificPattern::None:
        break;
    }
    return nullptr;
}

ALWAYS_INLINE JSString* replaceUsingRegExpSearch(VM& vm, JSGlobalObject* globalObject, JSString* string, JSValue searchValue, const CallData& callData, const String& replacementString, JSValue replaceValue)
{
    auto scope = DECLARE_THROW_SCOPE(vm);

    auto source = string->value(globalObject);
    RETURN_IF_EXCEPTION(scope, nullptr);

    unsigned sourceLen = source->length();
    RegExpObject* regExpObject = jsCast<RegExpObject*>(searchValue);
    RegExp* regExp = regExpObject->regExp();
    bool global = regExp->global();
    bool hasNamedCaptures = regExp->hasNamedCaptures();

    if (global) {
        // ES5.1 15.5.4.10 step 8.a.
        regExpObject->setLastIndex(globalObject, 0);
        RETURN_IF_EXCEPTION(scope, nullptr);

        if (callData.type == CallData::Type::None && !replacementString.length())
            RELEASE_AND_RETURN(scope, removeUsingRegExpSearch(vm, globalObject, string, source, regExp));

        if (callData.type == CallData::Type::JS && !hasNamedCaptures && sourceLen >= Options::thresholdForStringReplaceCache())
            RELEASE_AND_RETURN(scope, replaceUsingRegExpSearchWithCache(vm, globalObject, string, source, regExp, jsCast<JSFunction*>(replaceValue)));
    }

    if (callData.type == CallData::Type::None) {
        switch (regExp->specificPattern()) {
        case Yarr::SpecificPattern::TrailingSpacesPlus:
        case Yarr::SpecificPattern::LeadingSpacesPlus:
        case Yarr::SpecificPattern::TrailingSpacesStar:
        case Yarr::SpecificPattern::LeadingSpacesStar: {
            if (!replacementString.isEmpty())
                break;

            if (auto* result = tryTrimSpaces(vm, globalObject, source, string, regExp))
                return result;

            break;
        }
        case Yarr::SpecificPattern::Atom:
        case Yarr::SpecificPattern::None:
            break;
        }
    }

    size_t lastIndex = 0;
    unsigned startPosition = 0;

    Vector<Range<int32_t>, 16> sourceRanges;
    Vector<String, 16> replacements;

    // This is either a loop (if global is set) or a one-way (if not).
    if (global && callData.type == CallData::Type::JS) {
        // regExp->numSubpatterns() + 1 for pattern args, + 2 for match start and string
        int argCount = regExp->numSubpatterns() + 1 + 2;
        if (hasNamedCaptures)
            ++argCount;
        JSFunction* func = jsCast<JSFunction*>(replaceValue);
        CachedCall cachedCall(globalObject, func, argCount);
        RETURN_IF_EXCEPTION(scope, nullptr);
        while (true) {
            int* ovector;
            MatchResult result = globalObject->regExpGlobalData().performMatch(globalObject, regExp, string, source, startPosition, &ovector);
            RETURN_IF_EXCEPTION(scope, nullptr);
            if (!result)
                break;

            if (UNLIKELY(!sourceRanges.tryConstructAndAppend(lastIndex, result.start)))
                OUT_OF_MEMORY(globalObject, scope);

            cachedCall.clearArguments();
            JSObject* groups = hasNamedCaptures ? constructEmptyObject(vm, globalObject->nullPrototypeObjectStructure()) : nullptr;

            for (unsigned i = 0; i < regExp->numSubpatterns() + 1; ++i) {
                int matchStart = ovector[i * 2];
                int matchLen = ovector[i * 2 + 1] - matchStart;

                JSValue patternValue;

                if (matchStart < 0)
                    patternValue = jsUndefined();
                else {
                    patternValue = jsSubstring(vm, globalObject, string, matchStart, matchLen);
                    RETURN_IF_EXCEPTION(scope, nullptr);
                }

                cachedCall.appendArgument(patternValue);

                if (i && hasNamedCaptures) {
                    String groupName = regExp->getCaptureGroupNameForSubpatternId(i);
                    if (!groupName.isEmpty()) {
                        auto captureIndex = regExp->subpatternIdForGroupName(groupName, ovector);

                        if (captureIndex == i)
                            groups->putDirect(vm, Identifier::fromString(vm, groupName), patternValue);
                        else if (captureIndex > 0) {
                            int captureStart = ovector[captureIndex * 2];
                            int captureLen = ovector[captureIndex * 2 + 1] - captureStart;
                            JSValue captureValue;
                            if (captureStart < 0)
                                captureValue = jsUndefined();
                            else {
                                captureValue = jsSubstring(vm, globalObject, string, captureStart, captureLen);
                                RETURN_IF_EXCEPTION(scope, nullptr);
                            }
                            groups->putDirect(vm, Identifier::fromString(vm, groupName), captureValue);
                        } else
                            groups->putDirect(vm, Identifier::fromString(vm, groupName), jsUndefined());
                    }
                }
            }

            cachedCall.appendArgument(jsNumber(result.start));
            cachedCall.appendArgument(string);
            if (hasNamedCaptures)
                cachedCall.appendArgument(groups);

            cachedCall.setThis(jsUndefined());
            if (UNLIKELY(cachedCall.hasOverflowedArguments())) {
                throwOutOfMemoryError(globalObject, scope);
                return nullptr;
            }

            JSValue jsResult = cachedCall.call();
            RETURN_IF_EXCEPTION(scope, nullptr);
            replacements.append(jsResult.toWTFString(globalObject));
            RETURN_IF_EXCEPTION(scope, nullptr);

            lastIndex = result.end;
            startPosition = lastIndex;

            // special case of empty match
            if (result.empty()) {
                startPosition++;
                if (startPosition > sourceLen)
                    break;
                if (U16_IS_LEAD(source[startPosition - 1]) && U16_IS_TRAIL(source[startPosition])) {
                    startPosition++;
                    if (startPosition > sourceLen)
                        break;
                }
            }
        }
    } else {
        do {
            int* ovector;
            MatchResult result = globalObject->regExpGlobalData().performMatch(globalObject, regExp, string, source, startPosition, &ovector);
            RETURN_IF_EXCEPTION(scope, nullptr);
            if (!result)
                break;

            if (callData.type != CallData::Type::None) {
                if (UNLIKELY(!sourceRanges.tryConstructAndAppend(lastIndex, result.start)))
                    OUT_OF_MEMORY(globalObject, scope);

                MarkedArgumentBuffer args;
                JSObject* groups = hasNamedCaptures ? constructEmptyObject(vm, globalObject->nullPrototypeObjectStructure()) : nullptr;

                for (unsigned i = 0; i < regExp->numSubpatterns() + 1; ++i) {
                    int matchStart = ovector[i * 2];
                    int matchLen = ovector[i * 2 + 1] - matchStart;

                    JSValue patternValue;

                    if (matchStart < 0)
                        patternValue = jsUndefined();
                    else {
                        patternValue = jsSubstring(vm, globalObject, string, matchStart, matchLen);
                        RETURN_IF_EXCEPTION(scope, nullptr);
                    }

                    args.append(patternValue);

                    if (i && hasNamedCaptures) {
                        String groupName = regExp->getCaptureGroupNameForSubpatternId(i);
                        if (!groupName.isEmpty()) {
                            auto captureIndex = regExp->subpatternIdForGroupName(groupName, ovector);

                            if (captureIndex == i)
                                groups->putDirect(vm, Identifier::fromString(vm, groupName), patternValue);
                            else if (captureIndex > 0) {
                                int captureStart = ovector[captureIndex * 2];
                                int captureLen = ovector[captureIndex * 2 + 1] - captureStart;
                                JSValue captureValue;
                                if (captureStart < 0)
                                    captureValue = jsUndefined();
                                else {
                                    captureValue = jsSubstring(vm, globalObject, string, captureStart, captureLen);
                                    RETURN_IF_EXCEPTION(scope, nullptr);
                                }
                                groups->putDirect(vm, Identifier::fromString(vm, groupName), captureValue);
                            } else
                                groups->putDirect(vm, Identifier::fromString(vm, groupName), jsUndefined());
                        }
                    }
                }

                args.append(jsNumber(result.start));
                args.append(string);
                if (hasNamedCaptures)
                    args.append(groups);
                if (UNLIKELY(args.hasOverflowed())) {
                    throwOutOfMemoryError(globalObject, scope);
                    return nullptr;
                }

                JSValue replacement = call(globalObject, replaceValue, callData, jsUndefined(), args);
                RETURN_IF_EXCEPTION(scope, nullptr);
                String replacementString = replacement.toWTFString(globalObject);
                RETURN_IF_EXCEPTION(scope, nullptr);
                replacements.append(replacementString);
                RETURN_IF_EXCEPTION(scope, nullptr);
            } else {
                int replLen = replacementString.length();
                if (lastIndex < result.start || replLen) {
                    if (UNLIKELY(!sourceRanges.tryConstructAndAppend(lastIndex, result.start)))
                        OUT_OF_MEMORY(globalObject, scope);

                    if (replLen) {
                        StringBuilder replacement(OverflowPolicy::RecordOverflow);
                        substituteBackreferences(replacement, replacementString, source, ovector, regExp);
                        if (UNLIKELY(replacement.hasOverflowed()))
                            OUT_OF_MEMORY(globalObject, scope);
                        replacements.append(replacement.toString());
                    } else
                        replacements.append(String());
                }
            }

            lastIndex = result.end;
            startPosition = lastIndex;

            // special case of empty match
            if (result.empty()) {
                startPosition++;
                if (startPosition > sourceLen)
                    break;
                if (U16_IS_LEAD(source[startPosition - 1]) && U16_IS_TRAIL(source[startPosition])) {
                    startPosition++;
                    if (startPosition > sourceLen)
                        break;
                }
            }
        } while (global);
    }

    if (!lastIndex && replacements.isEmpty())
        return string;

    if (static_cast<unsigned>(lastIndex) < sourceLen) {
        if (UNLIKELY(!sourceRanges.tryConstructAndAppend(lastIndex, sourceLen)))
            OUT_OF_MEMORY(globalObject, scope);
    }
    RELEASE_AND_RETURN(scope, jsSpliceSubstringsWithSeparators(globalObject, string, source, sourceRanges.data(), sourceRanges.size(), replacements.data(), replacements.size()));
}

ALWAYS_INLINE JSString* replaceUsingRegExpSearch(VM& vm, JSGlobalObject* globalObject, JSString* string, JSValue searchValue, JSValue replaceValue)
{
    auto scope = DECLARE_THROW_SCOPE(vm);

    String replacementString;
    auto callData = JSC::getCallData(replaceValue);
    if (callData.type == CallData::Type::None) {
        replacementString = replaceValue.toWTFString(globalObject);
        RETURN_IF_EXCEPTION(scope, nullptr);
    }

    RELEASE_AND_RETURN(scope, replaceUsingRegExpSearch(
        vm, globalObject, string, searchValue, callData, replacementString, replaceValue));
}

inline bool checkObjectCoercible(JSValue thisValue)
{
    if (thisValue.isString())
        return true;

    if (thisValue.isUndefinedOrNull())
        return false;

    if (thisValue.isObject() && asObject(thisValue)->isEnvironment())
        return false;

    return true;
}

ALWAYS_INLINE JSString* replace(VM& vm, JSGlobalObject* globalObject, JSValue thisValue, JSValue searchValue, JSValue replaceValue, StringReplaceMode replaceMode)
{
    auto scope = DECLARE_THROW_SCOPE(vm);

    if (UNLIKELY(!checkObjectCoercible(thisValue))) {
        throwVMTypeError(globalObject, scope);
        return nullptr;
    }
    JSString* string = thisValue.toString(globalObject);
    RETURN_IF_EXCEPTION(scope, nullptr);

    JSString* searchJSString = searchValue.isString() ? asString(searchValue) : nullptr;
    JSString* replaceJSString = replaceValue.isString() ? asString(replaceValue) : nullptr;

    if (searchValue.inherits<RegExpObject>())
        RELEASE_AND_RETURN(scope, replaceUsingRegExpSearch(vm, globalObject, string, searchValue, replaceValue));

    if (searchJSString && replaceJSString) {
        if (JSString* result = tryReplaceOneCharUsingString<DollarCheck::Yes>(globalObject, string, searchJSString, replaceJSString))
            return result;
        RETURN_IF_EXCEPTION(scope, nullptr);
    }

    auto thisString = string->value(globalObject);
    RETURN_IF_EXCEPTION(scope, nullptr);

    // This path avoids an extra ref count churn for the most likely case that the search value is a string.
    if (LIKELY(searchJSString)) {
        auto searchString = searchJSString->value(globalObject);
        RETURN_IF_EXCEPTION(scope, nullptr);

        RELEASE_AND_RETURN(scope, replaceUsingStringSearch(vm, globalObject, string, thisString, WTFMove(searchString), replaceValue, replaceMode));
    }

    String searchString = searchValue.toWTFString(globalObject);
    RETURN_IF_EXCEPTION(scope, nullptr);

    RELEASE_AND_RETURN(scope, replaceUsingStringSearch(vm, globalObject, string, thisString, WTFMove(searchString), replaceValue, replaceMode));
}

} // namespace JSC

WTF_ALLOW_UNSAFE_BUFFER_USAGE_END
