# -*- coding: utf-8 -*-

'''
----------------
- Globals
----------------
'''
import sys
g_dbg = ('-dbg' in sys.argv) or False

'''
----------------
- Parser
----------------
'''
import copy
from sets import Set
def uni_pr(str):
		return str.encode('utf-8')
def parse_pp_toks(toks, join_ws = ' '):
	return join_ws.join([u"{}".format(tok[1]) for tok in toks if len(tok[1])])
def parse_pp_indexed_toks(toks, toksi):
	return ' '.join([u"{}".format(toks[i][1]) for i in toksi if len(toks[i][1])])
def parse_tok_group_toks(group, tl):
	els = []
	for p in group['parts']:
		if (type(p) is not list):
			els.extend(parse_tok_group_toks(p, tl))
		else:
			els.extend([tl[x] for x in p])
	return els
def parse_pp_group_toks(group, tl, join_ws=' '):
	return parse_pp_toks(parse_tok_group_toks(group, tl), join_ws)
def parse_tok_print_group(group, tl, depth=0):
	for p in group['parts']:
		if (type(p) is not list):
			parse_tok_print_group(p, tl, depth+1)
		else:
			print uni_pr(u'{}{} {}'.format(''.join([' ']*(depth)), '{}|_'.format(' ' if depth-1 else '') if depth else '', parse_pp_indexed_toks(tl,p)))
def parse_tok_get_simple_group_seplist(g, tl):
	sepl = g['parts'][0] if len(g['parts']) == 1 else g['parts'][1]
	return [x for x in sepl if tl[x][0] != ',']
def parse_tok_group_to_str(group, tl):
	return ''.join([x[1] for x in parse_tok_group_toks(group, tl)])
def parse_group_is_trivial(group, pre_is_func):
	return not pre_is_func and (len(group['parts']) == 3 and (type(group['parts'][1]) is list and len(group['parts'][1]) == 1))
def parse_group_is_simple(group, pre_is_func):
	return parse_group_is_trivial(group, pre_is_func) or len(group['parts']) == 3 and type(group['parts'][1]) is not list
def parse_group_match_group_seps(group, tl, gsep_pairs, gsep_open):
	for p in group['parts']:
		if (type(p) is not list):
			if not parse_group_match_group_seps(p, tl, gsep_pairs, gsep_open):
				return False
		else:
			for ti in p:
				if tl[ti][0] == '[':
					gsep_pairs.append([ti,None]); gsep_open[0] = len(gsep_pairs)-1;
				elif tl[ti][0] == ']':
					if gsep_open[0] < 0:
						return False
					gsep_pairs[gsep_open[0]][1] = ti;
					while gsep_open[0] >= 0 and (gsep_pairs[gsep_open[0]][1] is not None):
						 gsep_open[0] = gsep_open[0]-1;
	return True
def parse_root_group_match_group_seps(root, tl):
	gsep_pairs = []; gsep_open = [-1];
	success = parse_group_match_group_seps(root, tl, gsep_pairs, gsep_open)
	return (success and gsep_open[0] == -1), gsep_pairs
def parse_in_place_group_rem_toks(group, tl, rem_tl, rem_i):
	for gpi in range(len(group['parts'])):
		p = group['parts'][gpi]
		rem_p_local = []
		if (type(p) is not list):
			rem_i = parse_in_place_group_rem_toks(p, tl, rem_tl, rem_i)
		else:
			rem_ti_local = []
			for pii in range(len(p)):
				if rem_i < len(rem_tl) and p[pii] == rem_tl[rem_i]:
					rem_ti_local.append(pii); rem_i = rem_i+1;
			for ri in reversed(rem_ti_local):
				p.pop(ri)
		if len(p) == 0:
			rem_p_local.append(gpi)
	for ri in reversed(rem_p_local):
		group['parts'].pop(ri)
	return rem_i
def parse_root_group_rem_toks(root, tl, rem_tl):
	ngroup = copy.deepcopy(root); parse_in_place_group_rem_toks(ngroup, tl, sorted(rem_tl), 0); return ngroup;
def parse_root_group_reduce(root, tl):
	ok_gseps, gsep_pairs = parse_root_group_match_group_seps(root, tl)
	if not ok_gseps:
		return False, None
	rem_pairs_inds = Set()
	for pi in range(len(gsep_pairs)-1):
		pair_i = gsep_pairs[pi]
		for pj in range(pi+1, len(gsep_pairs)):
			pair_j = gsep_pairs[pj]
			if pair_i[0] == pair_j[0]-1 and pair_i[1] == pair_j[1]+1:
				rem_pairs_inds.add(tuple(pair_j))
			else:
				break
	rem_toks = sorted(list(sum(list(rem_pairs_inds), ())))
	return True, parse_root_group_rem_toks(root, tl, rem_toks)
def parse_group(tl, tli, tlo, depth):
	group = { 'parts':[], 'first_tok':tli, 'last_tok':-1 }; started = False;
	while tli < len(tl):
		tok = tl[tli]
		if (tok[0] == ']'):
			group['parts'].append([tli]); group['last_tok']=tli; tlo[0] = tli+1; return group if (started) else None;
		elif (tok[0] == '['):
			if started:
				ngtlo = [0]; ng = parse_group(tl, tli, ngtlo, depth+1);
				if ng:
					tli = ngtlo[0]-1; group['parts'].append(ng);
				else:
					return None
			else:
				group['parts'].append([tli]); started = True;
		else:
			if started:
				if len(group['parts']) <= 1 or (type(group['parts'][-1]) is not list):
					group['parts'].append([])
				group['parts'][-1].append(tli)
			else:
				if (tok[0] != 'ws'):
					return None
		#print depth, started, group, tli, tl
		tli = tli+1
	return None
def parse_root_group(tl):
	gtl = [('[','(','')] + tl + [(']',')','')]
	tlo = [0]; root = parse_group(gtl, 0, tlo, 0);
	rest_is_ws = all( tl[x][0]=='w' for x in range(tlo[0], len(tl)) )
	success_reduce, g_reduced = parse_root_group_reduce(root, gtl)
	return gtl, g_reduced if (root and rest_is_ws and success_reduce) else None
def parse_refine_toks(toks, const_map):
		ntoks = copy.deepcopy(toks)
		for ti in range(len(ntoks)):
				tok = ntoks[ti]
				if tok[0] == 's' and tok[2] == '':
						if ti+1<len(ntoks) and ntoks[ti+1][0] == '[':
								tok[2] = 'func'
						elif tok[1] in const_map:
								tok[2] = 'const'
						else:
								tok[2] = 'cvar' if (tok[1].upper() == tok[1] and tok[1].upper() != tok[1].lower() ) else 'var'
		return ntoks
def parse_tokenize(func_str, ops, parse_strict = True, const_map = {}):
		def is_float(s):
				try:
						float(s)
						return True
				except ValueError:
						return False
		def has_ws(token):
				return ''.join(token.split()) != token
		def is_number(token, final = True, leaf = None):
				return not has_ws(token) and (not (token.startswith('+') or token.startswith('-'))) and (is_float(token) if final else is_float(token+'0'))
		def is_symbol(token, final = True, leaf = None):
				tl = token[-1]
				return not has_ws(token) and not (is_separator(tl) or is_operator(tl) or is_group_start(tl) or is_group_end(tl) or (is_number(token.strip(), True) if final else False) )
		def is_symbol_restricted(token, final = True, leaf = None):
				return token[:1].isalpha() and is_symbol(token, final, leaf)
		def is_operator(token, final = True, leaf = None):
				if token in ops:
						return True
		def is_separator(token, final = True, leaf = None):
				if token in [',']:
						return True
		def is_ws(token, final = True, leaf = None):
				if len(token.strip()) == 0:
						return True
		def is_group_start(token, final = True, leaf = None):
				return token in ['[','(']
		def is_group_end(token, final = True, leaf = None):
				return token in [']',')']
		def print_group(group, tl, depth=0):
				return parse_tok_print_group(group, tl, depth)
		def group_to_str(group, tl):
				return parse_tok_group_to_str(group, tl)
		token_tests = { 'n':is_number, 's':is_symbol_restricted if parse_strict else is_symbol, 'o':is_operator, 'w':is_ws, ',':is_separator, '[':is_group_start, ']':is_group_end }
		root = {'parent':None, 'children':[], 'token':['?','',''] }
		pre_leafs = [root]
		for ch in func_str if isinstance(func_str, unicode) else unicode(func_str, 'utf-8'):
				if unicode(ch.encode("ascii","ignore"), 'utf-8') == ch:
						ch = ch.encode("ascii","ignore")
				#else:
				#    print 'uni:', ch
				#print 'ch', ch
				post_leafs = []
				for leaf in pre_leafs:
						tp,to,tr = leaf['token']
						nto = to+ch
						if (tp != '?'):
								if token_tests[tp](nto, False, leaf):
										leaf['token'][1] = nto
										post_leafs.append(leaf)
								else:
										if token_tests[tp](to, True, leaf):
												for ttp,tt in token_tests.items():
														if tt(ch, False, leaf):
																nl = {'parent':leaf, 'children':[], 'token':[ttp, ch, ''] }
																leaf['children'].append(nl); post_leafs.append(nl);
						else:
								cands = []
								for ttp,tt in token_tests.items():
										if tt(nto, False, leaf):
												cands.append(ttp)
								if len(cands) == 1:
										leaf['token'][0] = cands[0]; leaf['token'][1] = nto;
										post_leafs.append(leaf)
								elif len(cands) > 1:
										for c in cands:
												nl = {'parent':leaf if len(leaf['token'][1]) else None, 'children':[], 'token':[c, nto, ''] }
												leaf['children'].append(nl); post_leafs.append(nl);
				pre_leafs = post_leafs
		if g_dbg:
				print uni_pr(u'Dbg: parsing [{}]'.format(func_str if isinstance(func_str, unicode) else unicode(func_str, 'utf-8')))
		valid_token_lists = []
		for leaf in pre_leafs:
				tp,to,tr = leaf['token']
				if (tp != '?' and token_tests[tp](to, True, leaf)):
						token_list = []
						while leaf:
								token_list.append(leaf['token']); leaf = leaf['parent'];
						valid_token_lists.append(parse_refine_toks(list(reversed(token_list)), const_map))
		no_ws_token_lists = []
		for tl in valid_token_lists:
				ptl = []
				for tli in range(len(tl)):
						if tl[tli][0] != 'w':
								ptl.append(tl[tli])
				no_ws_token_lists.append(ptl)
		auto_op_token_lists = []
		for tl in no_ws_token_lists:
				ptl = []
				for tli in range(len(tl)):
						if tl[tli][0] in ['n', 's']:
								if tli+1<len(tl) and tl[tli+1][0] in ['n', 's']:
										ptl.append(tl[tli]); ptl.append(('o','*',''));
								elif tli-1>0 and tl[tli-1][0] in [']']:
										ptl.append(('o','*','')); ptl.append(tl[tli]);
								elif tl[tli][2] != 'func' and tli+1<len(tl) and tl[tli+1][0] == '[':
										ptl.append(tl[tli]); ptl.append(('o','*',''));
								else:
										ptl.append(tl[tli])
						elif tl[tli][0] == ']' and tli+1<len(tl) and tl[tli+1][0] == '[':
								ptl.append(tl[tli]); ptl.append(('o','*',''));
						else:
								ptl.append(tl[tli])
				auto_op_token_lists.append(ptl)
		processed_token_lists = auto_op_token_lists
		valid_group_trees = []
		for tl in processed_token_lists:
				gtl, tl_group = parse_root_group(tl)
				if (tl_group):
						#print_group(tl_group, gtl); print '';
						valid_group_trees.append((gtl, tl_group))
		if len(valid_group_trees) == 0:
				if g_dbg:
						print 'Note: invalid expression'
				return (None, None)
		lbd_less_tokens = lambda x,y: len(x[0])-len(y[0])
		sorted_group_trees = sorted(valid_group_trees, cmp=lbd_less_tokens)
		if len(sorted_group_trees)>1 and lbd_less_tokens(sorted_group_trees[0], sorted_group_trees[1]) == 0:
				if g_dbg:
						print 'Note: ambiguous expression'
				return (None, None)
		gt = sorted_group_trees[0]
		if g_dbg:
				print_group(gt[1], gt[0])
				print uni_pr(parse_pp_toks( parse_tok_group_toks(gt[1], gt[0])))
				#print group_to_str(gt[1], gt[0])
		return gt[1], gt[0] # group_tree, toks
'''
----------------
- Logic
----------------
'''
k_logical_op_and = [u'∧', '&']
k_logical_op_or = ['v']
k_logical_ops = [k_logical_op_and, k_logical_op_or]
k_logical_ops_flat = reduce(lambda x,y: x+y, k_logical_ops)
def parse_to_canonical_op_symbols(tree_toks):
	can_table = {}
	for lop in k_logical_ops:
		for i in range(len(lop)):
			can_table[lop[i]] = lop[0]
	for tok in tree_toks[1]:
		if tok[0] == 'o':
			tok[1] = can_table.get(tok[1], tok[1])
def parse_find_top_op_tok_index(tree_toks):
	len_to_op = {5:2, 3:1}
	n = len(tree_toks[0]['parts'])
	print n
	if n in len_to_op:
		op_tok = tree_toks[0]['parts'][len_to_op[n]]
		if tree_toks[1][op_tok[0]][0] == 'o':
			return op_tok[0]
	return -1
def rule_IA(a, b):
		return '({} ∧ {})'.format(a,b)
#def can_rule_IE_L(a):
def rule_IE_L(a):
		return '({} ∧ {})'.format(a,b)
def rule_IE_R(a):
		return '({} ∧ {})'.format(a,b)
k_uni_rules = [
		('∧E', rule_IE_L),
		('∧E', rule_IE_R)
]
k_bin_rules = [
		('∧I', rule_IA)
]
'''
----------------
- Main
----------------
'''
import os, sys
#os.system('chcp 65001')
expr_tree_toks = parse_tokenize(sys.argv[1], k_logical_ops_flat)
if g_dbg:
	parse_tok_print_group(*expr_tree_toks)
	print expr_tree_toks[0]['parts']
	print expr_tree_toks[1]
parse_to_canonical_op_symbols(expr_tree_toks)
parse_tok_print_group(*expr_tree_toks)
top_tok_i = parse_find_top_op_tok_index(expr_tree_toks)
if top_tok_i != -1:
	print expr_tree_toks[1][top_tok_i]