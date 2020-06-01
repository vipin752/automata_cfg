# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 01:07:31 2020

@author: vipin
"""
from __main__ import app, request, render_template
import copy
import uuid
import string

# Class designed for state of cfg production rule automation.

CAT_SYM = '.'
UNI_SYM = '+'
KLE_SYM = '*'
ETY_STR_SYM = '1'
ALPHABET = set(string.ascii_letters)
REGEX_SYM = ALPHABET.union({CAT_SYM, UNI_SYM, KLE_SYM})

class State():
    def __init__(self, state_id=None):
        def generate_id():
            return int(uuid.uuid4())

        self.id = generate_id() if state_id is None else state_id

    def get_id(self):
        return int(self.id)

    def __hash__(self):
        return self.get_id()

    def __eq__(self, other):
        return self.get_id() == other.get_id()

    def __cmp__(self, other):
        if self.get_id() < other.get_id():
            return -1
        elif self.get_id() > other.get_id():
            return 1
        else:
            return 0

    def __str__(self):
        return str(self.get_id())[:5]


class FiniteAutomation:
    def __init__(self):
        self.start_state = None
        self.finish_state = None
        self.move = None

    # Return set of state nearStr by symbol
    def go(self, state, symbol):
        return frozenset(self.move.get(state, {}).get(symbol, {}))

    def get_start_state(self):
        return copy.copy(self.start_state)

    def get_finish_state(self):
        return copy.copy(self.finish_state)

    def __str__(self):
        res = "start: {0}\n".format(self.get_start_state())
        res += "finish: {0}\n".format(self.get_finish_state())
        for state, sym_strState in self.move.items():
            for symbol, neighbor_set in sym_strState.items():
                for neighbor in neighbor_set:
                    res += "({0}, {1}, {2})\n".format(state, symbol, neighbor)
        return res


class NFA(FiniteAutomation):

    def __init__(self, postfix_regex):
        super().__init__()
        validate_regx_exprssn(postfix_regex)
        self.postfix_regex = postfix_regex
        if len(postfix_regex) <= 1:

            self.start_state = State()
            self.finish_state = State()
            self.move = {self.start_state: {postfix_regex: {self.finish_state}}}
        else:
            
            self.start_state = None
            self.finish_state = None
            self.move = None
            self.__prepare_automation()

    def __prepare_automation(self):
        def concat_lft_rgt(left, right):
            left.move[left.finish_state] = right.move[right.start_state]
            left.move = dict(list(left.move.items()) + list(right.move.items()))
            del left.move[right.start_state]
            left.finish_state = right.finish_state
            return left

        def union(left, right):
            left.move = dict(list(left.move.items()) + list(right.move.items()))
            new_start_state = State()
            new_finish_state = State()
            left.move[new_start_state] = {"": {left.start_state, right.start_state}}
            left.move[left.finish_state] = {"": {new_finish_state}}
            left.move[right.finish_state] = {"": {new_finish_state}}
            left.start_state = new_start_state
            left.finish_state = new_finish_state
            return left

        def kleene(what):
            new_start_state = State()
            new_finish_state = State()
            what.move[new_start_state] = {"": {new_finish_state, what.start_state}}
            what.move[what.finish_state] = {"": {what.start_state, new_finish_state}}
            what.start_state = new_start_state
            what.finish_state = new_finish_state
            return what


        stk = []
        for symbol in self.postfix_regex:
            if symbol in ALPHABET:
                stk.append(NFA(symbol))
            elif symbol == CAT_SYM:
                right_nfa = stk.pop()
                left_nfa = stk.pop()
                stk.append(concat_lft_rgt(left_nfa, right_nfa))
            elif symbol == UNI_SYM:
                right_nfa = stk.pop()
                left_nfa = stk.pop()
                stk.append(union(left_nfa, right_nfa))
            elif symbol == KLE_SYM:
                automation = stk.pop()
                stk.append(kleene(automation))
        
        res = stk.pop()
        self.start_state = res.start_state
        self.finish_state = res.finish_state
        self.move = res.move

    def get_postfix_regex(self):
        return self.postfix_regex
    
    def validate_given_word(self, word):
        state = self.start_state
        for char in word:
            state = self.go(state, char)
            if len(state) == 0:
                return False
            else:
                state = set(state).pop()
        if state in self.finish_state:
            return True
        else:
            return False


class DFA(FiniteAutomation):
    def __init__(self, build_from):
        super().__init__()
        self.move = {}
        if isinstance(build_from, str):
            validate_regx_exprssn(build_from)
            self.postfix_regex = build_from
            nfa = NFA(self.postfix_regex)
        elif isinstance(build_from, NFA):
            self.postfix_regex = build_from.get_postfix_regex()
            nfa = build_from
        else:
            raise SyntaxError
        self.__generate_using_nfa(nfa)

    def __generate_using_nfa(self, nfa):
        self.start_state = get_epln_clsr(nfa, {nfa.get_start_state()})
        self.move[self.start_state] = {}
        unmarked_states = [self.start_state]
        self.finish_state = set()
        if nfa.get_finish_state() in self.start_state:
            self.finish_state.add(frozenset(self.start_state))
        while len(unmarked_states) > 0:
            unmarked_state = unmarked_states.pop(0)
            for char in ALPHABET:
                adj_nearStr = set()
                for state in unmarked_state:
                    adj_nearStr = adj_nearStr.union(nfa.go(state, char))
                if len(adj_nearStr) > 0:
                    nearStr_set = get_epln_clsr(nfa, adj_nearStr)
                    if len(nearStr_set) > 0:
                        if nearStr_set not in self.move.keys():
                            unmarked_states.append(nearStr_set)
                            self.move[nearStr_set] = {}
                        self.move[unmarked_state][char] = {nearStr_set}
                        if nfa.get_finish_state() in nearStr_set:
                            self.finish_state.add(frozenset(nearStr_set))
        self.finish_state = frozenset(self.finish_state)

    def validate_given_word(self, word):
        state = self.start_state
        for char in word:
            state = self.go(state, char)
            if len(state) == 0:
                return False
            else:
                state = set(state).pop()
        if state in self.finish_state:
            return True
        else:
            return False

    def __str__(self):
        def get_updated_val(states_set):
            name = ""
            for state in states_set:
                name += str(state) + " "
            return name

        def get_finish_state_name(finish_state):
            name = ""
            for states_set in finish_state:
                name += "{" + "{0}".format(get_updated_val(states_set)) + "} "
            return name
        res = ""
        res += "start: {0}\n".format(get_updated_val(self.get_start_state()))
        res += "finish: {0}\n".format(get_finish_state_name(self.get_finish_state()))
        for states_set, sym_strState in self.move.items():
            for symbol, nearStr_set in sym_strState.items():
                for neighbor in nearStr_set:
                    res += "({0}, {1}, {2})\n".format(get_updated_val(states_set), symbol, get_updated_val(neighbor))
        return res


def validate_regx_exprssn(postfix_regex):
    counter = 0
    for symbol in postfix_regex:
        if symbol not in REGEX_SYM:
            raise SyntaxError
        elif symbol in ALPHABET:
            counter += 1
        elif symbol != KLE_SYM:
            counter -= 1
        if counter <= 0:
            raise SyntaxError("Invalid postfix notation")


#Remind: return frozenset!!

def get_epln_clsr(nfa, sts):
    stk = list(sts)
    clsr = set(sts)
    while len(stk) > 0:
        t = stk.pop()
        for sideStr in nfa.go(t, ""):
            if sideStr not in clsr:
                clsr.add(sideStr)
                stk.append(sideStr)
    return frozenset(clsr)

@app.route('/test', methods=['POST'])
def test():
    #values = [x for x in request.form.values()]
    grammer = request.form['grammer']
    print('grammer: ',grammer)
    rule = request.form['rule']
    word = request.form['text']
    
    if 'dfa' == grammer:
        dfa = DFA(rule)  # (aa)*b*(aa)*
        return render_template('index.html', test_result='Accepts DFA Rule: {} Text: {} --> {}'.format(rule,word,str(dfa.validate_given_word(word))))
    if 'nfa'== grammer:
        nfa = NFA(rule)  # 'ab+*'
        return render_template('index.html', test_result='Accepts NFA Rule: {} : Text: {} --> {}'.format(rule,word,str(nfa.validate_given_word(word))))
    #geeeting not defined exception by default dfa will call
    return render_template('index.html', test_result='{}'.format("Please select the grammer from given dropdown...."))
    