# Copyright (c)  2020  Mobvoi Inc.        (authors: Fangjun Kuang)
#
# See ../../../LICENSE for clarification regarding multiple authors

from copy import deepcopy
from typing import Union
from typing import List

from .fsa import Fsa
import _k2
import torch


def linear_fsa(symbols: Union[List[int], List[List[int]]]) -> Fsa:
    '''Construct an linear FSA from symbols.

    Note:
      The scores of arcs in the returned FSA are all 0.

    Args:
      symbols:
        A list of integers or a list of list of integers.

    Returns:
      An FSA if the input is a list of integers.
      A vector of FSAs if the input is a list of list of integers.
    '''
    ragged_arc = _k2.linear_fsa(symbols)
    return Fsa.from_ragged_arc(ragged_arc)


def top_sort(fsa: Fsa) -> Fsa:
    '''Sort an FSA topologically.

    Note:
      It returns a new FSA. The input FSA is NOT changed.

    Args:
      fsa:
        The input FSA to be sorted. It can be either a single FSA
        or a vector of FSAs.
    Returns:
      It returns a single FSA if the input is a single FSA; it returns
      a vector of FSAs if the input is a vector of FSAs.
    '''
    need_arc_map = True
    ragged_arc, arc_map = _k2.top_sort(fsa.arcs, need_arc_map=need_arc_map)
    arc_map = arc_map.to(torch.int64)  # required by index_select
    sorted_fsa = Fsa.from_ragged_arc(ragged_arc)
    for name, value in fsa.named_tensor_attr():
        setattr(sorted_fsa, name, value.index_select(0, arc_map))
    for name, value in fsa.named_non_tensor_attr():
        setattr(sorted_fsa, name, deepcopy(value))
    return sorted_fsa


def intersect(a_fsa: Fsa, b_fsa: Fsa) -> Fsa:
    '''Compute the intersection of two FSAs.

    Note:
      Intersection is also known as compose in FST.

    Args:
      a_fsa:
        The first input FSA. It can be either a single FSA or a vector of FSAs.
      b_fsa:
        The second input FSA. It can be either a single FSA or a vector of FSAs.

    Returns:
      The result of intersecting a_fsa and b_fsa.
    '''
    need_arc_map = True
    ragged_arc, a_arc_map, b_arc_map = _k2.intersect(a_fsa.arcs, b_fsa.arcs,
                                                     need_arc_map)
    a_arc_map = a_arc_map.to(torch.int64)  # required by index_select
    b_arc_map = b_arc_map.to(torch.int64)

    out_fsa = Fsa.from_ragged_arc(ragged_arc)
    for name, a_value in a_fsa.named_tensor_attr():
        # TODO(fangjun): what if b_fsa does not have the `name` attribute?
        if hasattr(b_fsa, name):
            b_value = getattr(b_fsa, name)
            # TODO(fangjun): this does not support aux_labels!
            assert a_value.dtype == b_value.dtype == torch.float32
            value = a_value.index_select(0, a_arc_map) \
                    + b_value.index_select(0, b_arc_map)
            setattr(out_fsa, name, value)

    for name, a_value in a_fsa.named_non_tensor_attr():
        setattr(out_fsa, name, a_value)

    for name, b_value in b_fsa.named_non_tensor_attr():
        if not hasattr(out_fsa, name):
            setattr(out_fsa, name, b_value)

    return out_fsa


def connect(fsa: Fsa) -> Fsa:
    '''Connect an FSA.

    Removes states that are neither accessible nor co-accessible.

    Note:
      A state is not accessible if it is not reachable from the start state.
      A state is not co-accessible if it cannot reach the final state.

    Args:
      fsa:
        The input FSA to be connected.

    Returns:
      An FSA that is connected.
    '''

    need_arc_map = True
    ragged_arc, arc_map = _k2.connect(fsa.arcs, need_arc_map=need_arc_map)
    arc_map = arc_map.to(torch.int64)  # required by index_select
    out_fsa = Fsa.from_ragged_arc(ragged_arc)
    for name, value in fsa.named_tensor_attr():
        setattr(out_fsa, name, value.index_select(0, arc_map))
    for name, value in fsa.named_non_tensor_attr():
        setattr(out_fsa, name, deepcopy(value))
    return out_fsa


def arc_sort(fsa: Fsa) -> Fsa:
    '''Sort arcs of every state.

    Note:
      Arcs are sorted by labels first, and then by dest states.

    Args:
      fsa:
        The input FSA.
    Returns:
      The sorted FSA.
    '''
    need_arc_map = True
    ragged_arc, arc_map = _k2.arc_sort(fsa.arcs, need_arc_map=need_arc_map)
    arc_map = arc_map.to(torch.int64)  # required by index_select
    out_fsa = Fsa.from_ragged_arc(ragged_arc)
    for name, value in fsa.named_tensor_attr():
        setattr(out_fsa, name, value.index_select(0, arc_map))
    for name, value in fsa.named_non_tensor_attr():
        setattr(out_fsa, name, deepcopy(value))
    return out_fsa