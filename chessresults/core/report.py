# report.py
# Copyright 2008 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Generate a report comparing results with schedule.
"""
import re

from solentware_misc.api import utilities
from solentware_misc.api.null import Null

from .gameobjects import (
    MatchReport,
    MatchGame,
    Section,
    Game,
    Player,
    UnfinishedGame,
    code_in_name,
    )
from .gameresults import resultmap, NULL_PLAYER
from .eventparser import PLAYED_ON

cross_table_row = re.compile(''.join((
    '(?P<pin>\d*)\.?',
    '(?P<row>(?:\s+[wb]?[-+=~])* *\Z)')))
cross_table_result = re.compile(''.join((
    '(?P<colour>[wb]?)',
    '(?P<score>[-+=~])\Z')))
swiss_table_row = re.compile(''.join((
    '(?P<pin>\d*)\.?',
    '(?P<row>',
    '(?:\s+(?:x|--|def[-+]|bye[-=+]|[wb][123456789][0123456789]*[-=+pme]))*',
    ' *\Z)')))
swiss_table_result = re.compile(''.join((
    '(?P<notplayed>x|--|def[-+]|bye[-=+])\Z|',
    '(?P<colour>[wb])',
    '(?P<opponent>[123456789][0123456789]*)',
    '(?P<score>[-=+pme])\Z')))
match_name = re.compile(''.join((
    '(?P<hometeam>.*?)(?=\s[0-9]*(\.5)?\s*-\s*[0-9]*(\.5)?\s)',
    '(?P<score>\s[0-9]*(\.5)?\s*-\s*[0-9]*(\.5)?\s)',
    '(?P<awayteam>.*)\Z')))
game_result = re.compile(''.join((
    '(?:(?P<board>\d*(?:\.\d*)?)?',
    '(?P<colour>[w|b])?[ \t])?',
    '(?P<date_player>.*?[ \t]|[ \t]*)?',
    '(?P<score>dbld|def-|def[=+]|bye[=+]|draw|1-0|0-1|void|unfinished|default)',
    '(?P<player>[ \t].*)?\Z')))
individual_game_result = re.compile(''.join((
    '(?P<white>.*?)(?=\s[dD][rR][aA][wW]\s|\s1-0\s|\s0-1\s)',
    '(?P<score>\s[dD][rR][aA][wW]\s|\s1-0\s|\s0-1\s)',
    '(?P<black>.*)\Z')))

opposite_colour = {'w':'b', 'b':'w', '':''}
opposite_score = {'-':'+', 'm':'+', '=':'=', 'e':'=',
                  '+':'-', 'p':'-', '1':'0', '0':'1', 'x':'x', '~':'~'}

# BOARD_COLOUR defined for first-named team's players black on odd boards in
# first game (perhaps a multi-game rapidplay match ).
BOARD_COLOUR = {(True,): True,
                (False,): False,
                (None,): None,
                (True, True): False,
                (True, False): True,
                (True, None): None,              
                (False, True): True,
                (False, False): False,
                (False, None): None,
                (None, True): None,
                (None, False): None,
                (None, None): None,
                }
BOARD_COLOUR_REVERSE = {True:False, False:True, None:None}


class Report(object):

    """Results extracted from event report file containing one event.
    """

    def __init__(self):
        """Initialise results report attributes for events."""
        super().__init__()
        self.textlines = None
        self.error = []
        self.er_source = ''
        self.er_results = dict()
        self.er_matchresults = []
        self.er_unfinishedgames = []
        self.error_repeat = False
        self.er_section = dict()
        self.er_report_order = []
        self.er_name = None
        self.er_rounds = dict()
        self.er_pins = dict()
        self.er_players = dict()
        self.er_swiss_table = dict()
        self.er_team_number = dict()
        
    # set_match changed to populate er_matchresults in the way sl_report added
    # SLArticle.er_matchresults to SLReportWeekly.er_matchresults.  SLArticle
    # and SLReportWeekly are subclasses of ReportLeague.
    # Putting something in ReportLeague.er_results is left to collate_matches
    # method of Collation.
    def set_match(self, result):
        """Add match result entry to match result data structures."""

        # append not extend because matches are not batched by email instance.
        self.er_matchresults.append(result)
        
    def set_match_result(self, result):
        """Add match result entry to report data structures."""
        if result.competition not in self.er_results:
            self.er_results[result.competition] = dict()
        self.er_results[result.competition][
            (result.hometeam,
             result.awayteam,
             result.date,
             result.round,
             result.source,
             )] = result
        
    def build_results(self, textlines):
        """Populate the event results report from textlines."""

        def black_on_all(board):
            return False

        def black_on_odd(board):
            try:
                return BOARD_COLOUR[tuple([False if b[-1] in '13579' else
                                           True if b[-1] in '02468' else
                                           None
                                           for b in board.split('.')])]
            except:
                return None

        def colour_none(board):
            return None

        def white_on_all(board):
            return True

        def white_on_odd(board):
            try:
                return BOARD_COLOUR_REVERSE[black_on_odd(board)]
            except:
                return None
        
        def add_player_record(name, event, team, tagger):
            codes = set([s.strip() for s in code_in_name.findall(name)])
            name = ' '.join(
                [s.strip() for s in code_in_name.split(name)]).strip()
            key = (name, event, team)
            if key not in players:
                players[key] = Player(tagger=tagger,
                                      name=name,
                                      event=event,
                                      club=team,
                                      reported_codes=codes)
            if codes - players[key].reported_codes:
                players[key].add_reported_codes(codes)
            return players[key]

        def get_allplayall_games(text, tagger):
            spc = text.split()
            if spc[0] in sectiontypes:
                return get_section(text, tagger)
            elif spc[0] == 'source':
                get_source(spc)
                return get_allplayall_games
            ctr = cross_table_row.match(text)
            if ctr is None:
                tagger.append_generated_report(
                    self.error,
                    ''.join((
                        '"',
                        text,
                        '" is not recognised as a cross table row.\n')),
                    )
                self.error_repeat = False
                return get_allplayall_games
            get_crosstablerow_results(
                ctr.group('pin'),
                ctr.group('row'),
                tagger)
            return get_allplayall_games

        def get_crosstablerow_results(pin, row, tagger):
            cross_table = self.er_swiss_table[self._section]
            if len(pin):
                pin = int(pin)
            else:
                pin = len(cross_table) + 1
            row = row.split()
            if pin > len(row):
                tagger.append_generated_report(
                    self.error,
                    ''.join((
                        'PIN is greater than number of players implied in ',
                        'cross-table row "',
                        ' '.join((str(pin), self._section, ' '.join(row))),
                        '".\n')),
                    )
                self.error_repeat = False
                return
            if pin in cross_table:
                tagger.append_generated_report(
                    self.error,
                    ''.join((
                        'Cross-table row for PIN in "',
                        ' '.join((str(pin), self._section, ' '.join(row))),
                        '" already exists.\n')),
                    )
                self.error_repeat = False
                return
            card = []
            num_rounds = len(row)
            if num_rounds % 2 == 0:
                num_rounds -= 1
            for p in row:
                opponent_pin = len(card) + 1
                strm = cross_table_result.match(p)
                if strm is None:
                    tagger.append_generated_report(
                        self.error,
                        ''.join((
                            '"',
                            p,
                            '" in cross-table row "',
                            ' '.join((str(pin), self._section, ' '.join(row))),
                            '" is not a recognised result.\n')),
                        )
                    return False
                colour = strm.group('colour')
                score = strm.group('score')
                if opponent_pin == pin:
                    if p != '~':
                        tagger.append_generated_report(
                            self.error,
                            ''.join((
                                'Crosstable entry where opponent is self in "',
                                ' '.join((str(pin),
                                          self._section,
                                          ' '.join(row))),
                                '" must be "~".\n')),
                            )
                        continue
                    nominal_round = None
                else:
                    if opponent_pin > num_rounds:
                        if pin * 2 > opponent_pin:
                            nominal_round = (pin * 2) - opponent_pin
                        else:
                            nominal_round = (pin * 2) - 1
                    elif pin > num_rounds:
                        if opponent_pin * 2 > pin:
                            nominal_round = (opponent_pin * 2) - pin
                        else:
                            nominal_round = (opponent_pin * 2) - 1
                    else:
                        nominal_round = (pin + opponent_pin - 1) % num_rounds
                        if nominal_round == 0:
                            nominal_round = num_rounds
                if opponent_pin in cross_table:
                    # when opponent_pin == pin it will not be there
                    opponent_entry = cross_table[opponent_pin][pin - 1]
                    error = False
                    if score != opposite_score[opponent_entry['score']]:
                        error = True
                    if colour != opposite_colour[opponent_entry['colour']]:
                        error = True
                    if nominal_round != opponent_entry['nominal_round']:
                        error = True
                    if error:
                        tagger.append_generated_report(
                            self.error,
                            ''.join((
                                'Cross table row "',
                                ' '.join((str(pin),
                                          self._section,
                                          ' '.join(row))),
                                '") is not consistent with row for opponent "',
                                str(opponent_pin),
                                '".\n')),
                            )
                card.append(dict(
                    tagger=tagger,
                    colour=colour,
                    score=score,
                    nominal_round=nominal_round))
            cross_table[pin] = card
            return True

        def get_date(tokens, tagger, exact=True):
            datestr = ' '.join(tokens[1:])
            gdate = utilities.AppSysDate()
            d = gdate.parse_date(datestr)
            if d == len(datestr):
                self._date = gdate.iso_format_date()
                return d
            elif d < 0:
                tagger.append_generated_report(
                    self.error,
                    ''.join((
                        'Date not recognised in "',
                        ' '.join(tokens),
                        '".\n')),
                    )
            elif exact:
                tagger.append_generated_report(
                    self.error,
                    ''.join((
                        'Date found in "',
                        ' '.join(tokens),
                        '" but extra text is present.\n')),
                    )
            else:
                self._date = gdate.iso_format_date()
                return d
            return False

        def get_event_name(text, tagger):
            en = text.split()
            self.er_name = ' '.join(en)
            if self.er_name in self.er_section:
                tagger.append_generated_report(
                    self.error,
                    ''.join((
                        'Event name "',
                        self.er_name,
                        '" in "',
                        text,
                        '" is a duplicate.\n')),
                    )
            self.er_section[self.er_name] = None
            return get_section

        def get_game(text, tagger):
            gr = game_result.match(text)
            if gr is None:
                return False
            board = gr.group('board')
            if not board:
                board = str(len(self._games) + 1)
            colour = gr.group('colour')
            if not colour:
                colour = self._colourrule(board)
            gamescore = gr.group('score')
            if gamescore is not None:
                gamescore = resultmap.get(
                    gamescore.lower().strip(),
                    resultmap[None])
            awayplayer = gr.group('player')
            awayplayer = (
                '' if awayplayer is None else ' '.join(awayplayer.split()))
            if awayplayer:
                awayplayer = add_player_record(
                    awayplayer,
                    self.er_name,
                    self._match[1],
                    tagger)
            else:
                awayplayer = NullPlayer()
            date_player = gr.group('date_player')
            if date_player is not None:
                date_player = ' '.join(date_player.split())
                datetime = utilities.AppSysDate()
                d = datetime.parse_date(date_player)
                if d < 0:
                    gamedate = None
                else:
                    gamedate = datetime.iso_format_date()
                    date_player = date_player[d:].strip()
            else:
                gamedate = None
            if date_player:
                homeplayer = add_player_record(
                    date_player,
                    self.er_name,
                    self._match[0],
                    tagger)
            else:
                homeplayer = NullPlayer()

            if board not in self._games:
                if self._played_on is PlayedOnStatus.game_report_played_on:
                    self.er_unfinishedgames.append(UnfinishedGame(
                        tagger=tagger,
                        board=board,
                        date=gamedate,
                        homeplayer=homeplayer,
                        awayplayer=awayplayer,
                        result=gamescore,
                        homeplayerwhite=colour,
                        source=' '.join(
                            (self._match[4], self._section)).strip(),
                        section=self._section,
                        #competition='',
                        hometeam=self._match[0],
                        awayteam=self._match[1]))
                elif self._playerlimit:
                    c = self._match_homeplayers.setdefault(homeplayer, 0)
                    if c >= self._playerlimit:
                        tagger.append_generated_report(
                            self.error,
                            ''.join((
                                'Player "',
                                homeplayer.name,
                                '" in game "',
                                text,
                                '" occurs too many times in match.\n')),
                            )
                        self._match_homeplayers[homeplayer] += 1
                        c = self._match_awayplayers.setdefault(awayplayer, 0)
                        if c >= self._playerlimit:
                            tagger.append_generated_report(
                                self.error,
                                ''.join((
                                    'Player "',
                                    awayplayer.name,
                                    '" in game "',
                                    text,
                                    '" occurs too many times in match.\n')),
                                )
                        self._match_awayplayers[awayplayer] += 1
                    rsm = self.er_matchresults[-1]
                    rsm.games.append(MatchGame(
                        tagger=tagger,
                        board=board,
                        date=gamedate,
                        homeplayer=homeplayer,
                        awayplayer=awayplayer,
                        result=gamescore,
                        homeplayerwhite=colour))

                    # Do the check on number of times a player appears for full
                    # match report only.  When reporting played-on games assume
                    # repeated names are valid, and that problems will be seen
                    # because the report does not tally with a game originally
                    # reported unfinished.  If board numbers are not used in
                    # the reports the technique cannot work because the derived
                    # board numbers are likely wrong.
                    self._games[board] = rsm.games[-1]
                    
            else:
                rsm = self.er_matchresults[-1]
                inconsistent_game_report = False
                if (self._games[board].homeplayer != homeplayer or
                    self._games[board].awayplayer != awayplayer or
                    self._games[board].homeplayerwhite != colour or
                    gamedate != self._games[board].date):
                    inconsistent_game_report = True
                if self._games[board].result == '':
                    if gamescore != '':
                        self._games[board].result = gamescore
                elif self._games[board].result != gamescore:
                    inconsistent_game_report = True

                # Force an inconsistency to be reported as an error.
                if inconsistent_game_report:
                    rsm.games.append(MatchGame(
                        tagger=tagger,
                        board=board,
                        date=gamedate,
                        homeplayer=homeplayer,
                        awayplayer=awayplayer,
                        result=gamescore,
                        homeplayerwhite=colour))

            return True

        def get_games(text, tagger):
            gt = text.split()
            gt0 = gt[0].lower()
            if set_game_processing_rule(gt0):
                return get_matches
            elif gt0 == 'source':
                get_source(gt)
                return get_games
            elif gt0 == 'round':
                get_round(gt, tagger)
                return get_matches
            elif gt0 == 'date':
                get_date(gt, tagger)
                return get_matches
            elif gt0 == 'games':
                get_games_per_player_per_match(gt, tagger)
                return get_matches
            elif gt0 in sectiontypes:
                return get_section(text, tagger)
            elif gt0 == 'matchdefaulted':
                self.er_matchresults[-1].default = True
                return get_matches
            elif get_game(text, tagger):
                return get_games

            # The current self._played_on value does not apply once a failure
            # to find a game, when looking, occurs.
            #self._played_on = False

            if get_match(text, tagger):
                return get_games
            elif is_event_name_repeated(text):
                return get_matches
            else:
                tagger.append_generated_report(
                    self.error,
                    ''.join((
                        '"',
                        text,
                        '" in section "',
                        self._section,
                        '" is not recognised as a game result or match ',
                        'name.\n')),
                    )
            return get_matches

        def get_games_per_player_per_match(tokens, tagger):
            if len(tokens) != 2:
                tagger.append_generated_report(
                    self.error,
                    ''.join((
                        '"',
                        ' '.join(tokens),
                        '" must be like "games 2" to specify the number of ',
                        'times a player may appear in a match without a ',
                        'warning message being generated.\n')),
                    )
                return False
            if not tokens[-1].isdigit():
                tagger.append_generated_report(
                    self.error,
                    ''.join((
                        '"',
                        tokens[-1],
                        '" in "',
                        ' '.join(tokens),
                        '" must be digits to specify the number of ',
                        'times a player may appear in a match without a ',
                        'warning message being generated.\n')),
                    )
                return False
            self._playerlimit = int(tokens[-1])
            return True

        def get_individual_game(text, tagger):
            gi = individual_game_result.match(text)
            if gi is None:
                return False
            black = ' '.join(gi.group('black').split())
            gamescore = resultmap.get(
                gi.group('score').lower().strip(),
                resultmap[None])
            w_and_prefix = gi.group('white').split()
            gdate = utilities.AppSysDate()
            datestr = ' '.join(w_and_prefix)
            d = gdate.parse_date(datestr)
            if d < 0:
                gamedate = None
                white = datestr
            else:
                gamedate = gdate.iso_format_date()
                white = ' '.join(datestr[d:].split())
            white = add_player_record(white, None, None, tagger)
            black = add_player_record(black, None, None, tagger)
            if white.name == black.name:
                tagger.append_generated_report(
                    self.error,
                    ''.join((
                        'Player names in "',
                        text,
                        '" must be different.\n')),
                    )
                return False
            self.er_results[self._section].games.append(Game(
                tagger=tagger,
                result=gamescore,
                date=gamedate,
                homeplayerwhite=True,
                homeplayer=white,
                awayplayer=black))
            return True
        
        def get_individual_games(text, tagger):
            gt = text.split()
            gt0 = gt[0].lower()
            if gt0 in sectiontypes:
                return get_section(text, tagger)
            elif gt0 == 'source':
                get_source(gt)
                return get_individual_games
            if not get_individual_game(text, tagger):
                tagger.append_generated_report(
                    self.error,
                    ''.join((
                        '"',
                        text,
                        '" in section "',
                        self._section,
                        '" is not recognised as a game result.\n')),
                    )
            return get_individual_games

        def get_match(text, tagger):
            mn = match_name.match(text)
            if mn is None:
                return False
            awayteam = ' '.join(mn.group('awayteam').split())
            matchscore = mn.group('score').strip().lower().split('-')
            if len(matchscore) == 1:
                homescore = awayscore = None
            else:
                homescore = matchscore[0].rstrip()
                awayscore = matchscore[1].lstrip()
            ht_and_prefix = mn.group('hometeam').split()
            mdate = utilities.AppSysDate()
            datestr = ' '.join(ht_and_prefix)
            d = mdate.parse_date(datestr)
            if d < 0:
                if ht_and_prefix[0].isdigit():
                    matchround = str(int(ht_and_prefix.pop(0)))
                else:
                    matchround = self._round
                matchdate = self._date
                hometeam = datestr
            else:
                matchdate = mdate.iso_format_date()
                ht_and_prefix = datestr[d:].split()
                if ht_and_prefix[0].isdigit():
                    matchround = str(int(ht_and_prefix.pop(0)))
                else:
                    matchround = self._round
                hometeam = ' '.join(ht_and_prefix)
            if matchdate:
                source = ' '.join((matchdate, self._section))
            elif self.er_source:
                source = ' '.join((self.er_source, self._section)).strip()
            else:
                source = '' # or the tag name for the extracted data
            self._match = (
                hometeam, awayteam, matchdate, matchround, source)

            self._games = dict()
            if self._played_on is PlayedOnStatus.seek_played_on_report:
                self._played_on = PlayedOnStatus.game_report_played_on
            else:
                self._played_on = PlayedOnStatus.reports_not_played_on
                self.set_match(MatchReport(
                    order=len(self.er_matchresults),
                    tagger=tagger,
                    competition=self._section,
                    source=source,
                    date=matchdate, # added 2012-02-09
                    round=matchround,
                    hometeam=hometeam,
                    awayteam=awayteam,
                    homescore=homescore,
                    awayscore=awayscore,
                    default=False,
                    games=[]))
                self._match_homeplayers = dict()
                self._match_awayplayers = dict()
            return True

        def get_matches(text, tagger):
            mt = text.split()
            mt0 = mt[0].lower()
            if set_game_processing_rule(mt0):
                return get_matches
            elif mt0 == 'source':
                get_source(mt)
                return get_matches
            elif mt0 == 'round':
                get_round(mt, tagger)
                return get_matches
            elif mt0 == 'date':
                get_date(mt, tagger)
                return get_matches
            elif mt0 == 'games':
                get_games_per_player_per_match(mt, tagger)
                return get_matches
            elif mt0 in sectiontypes:
                return get_section(text, tagger)
            elif get_match(text, tagger):
                return get_games

            # The current self._played_on value does not apply once a failure
            # to find a match, when looking, occurs.
            #self._played_on = False

            if is_event_name_repeated(text):
                return get_matches
            else:
                tagger.append_generated_report(
                    self.error,
                    ''.join((
                        '"',
                        text,
                        '" in section "',
                        self._section,
                        '" is not recognised as a match name.\n')),
                    )
            return get_matches

        def get_round(tokens, tagger):
            if len(tokens) != 2:
                tagger.append_generated_report(
                    self.error,
                    ''.join((
                        '"',
                        ' '.join(tokens),
                        '" must be like "round 2" to specify the round.\n')),
                    )
                return False
            # Do not insist that round values are numbers.
            # Allow 'Semi-Final' and so on.
            try:
                self._round = str(int(tokens[-1]))
            except ValueError:
                self._round = tokens[-1]
            return True

        def get_section(text, tagger):

            # The current self._played_on value does not apply after looking
            # for a section name.  For example 'fixturelist Division 1'.
            #self._played_on = False

            s = text.split()
            st = s[0].lower()
            if st == 'source':
                get_source(st)
                return get_section
            if st not in sectiontypes:
                if self.error_repeat:
                    return get_section
                tagger.append_generated_report(
                    self.error,
                    ''.join((
                        'Section type "',
                        st,
                        '" not recognised.\n')),
                    )
                self.error_repeat = True
                return get_section
            if self.error_repeat:
                tagger.append_generated_report(
                    self.error,
                    ''.join((
                        'Section type "',
                        st,
                        '" found after errors.\n')),
                    )
                self.error_repeat = False
            self._section = ' '.join(s[1:])
            if self._section in self.er_section:
                if st != 'fixturelist':
                    tagger.append_generated_report(
                        self.error,
                        ''.join((
                            'Section "',
                            self._section,
                            '" named earlier.\n')),
                        )
                    self.error_repeat = True
                    return get_section
            if self._section not in self.er_section:
                self.er_section[self._section] = st
                self.er_report_order.append(self._section)
                sectiondata[st]()
            return sectiontypes[st]

        def get_swiss_pairing_card_results(pin, row, tagger):
            swiss_table = self.er_swiss_table[self._section]
            if len(pin):
                pin = int(pin)
            else:
                pin = len(swiss_table) + 1
            row = row.split()
            if pin in swiss_table:
                tagger.append_generated_report(
                    self.error,
                    ''.join((
                        'Swiss table row for PIN in "',
                        ' '.join((str(pin), self._section, ' '.join(row))),
                        '" already exists.\n')),
                    )
                self.error_repeat = False
                return

            card = []
            for p in row:
                strm = swiss_table_result.match(p)
                if strm is None:
                    tagger.append_generated_report(
                        self.error,
                        ''.join((
                            '"',
                            p,
                            '" in results "',
                            ' '.join(row),
                            '" pin "',
                            str(pin),
                            '" is not a recognised result.\n')),
                        )
                    return False
                colour = strm.group('colour')
                opponent_pin = strm.group('opponent')
                if opponent_pin is not None:
                    opponent_pin = int(opponent_pin)
                score = strm.group('score')
                if opponent_pin == pin:
                    tagger.append_generated_report(
                        self.error,
                        ''.join((
                            'Opponent pin in round "',
                            str(len(card) + 1),
                            '" of results ("',
                            ' '.join(row),
                            '" is same as pin ("',
                            str(pin),
                            '").\n')),
                        )
                    continue
                for p in swiss_table:
                    if len(swiss_table[p]) <= len(card):
                        continue #may be upgraded to error later
                    opponent_entry = swiss_table[p][len(card)]
                    error = False
                    if opponent_entry['opponent'] != pin:
                        if p == opponent_pin:
                            error = True
                    elif opponent_pin == p:
                        opponent_colour = opposite_colour[colour]
                        opponent_score = opposite_score[score]
                        if opponent_entry['colour'] != opponent_colour:
                            error = True
                        elif opponent_entry['score'] != opponent_score:
                            error = True
                    else:
                        error = True
                    if error:
                        tagger.append_generated_report(
                            self.error,
                            ''.join((
                                'Pairing card result for round "',
                                str(len(card) + 1),
                                '" ("',
                                ' '.join(row),
                                '" (pin "',
                                str(pin),
                                '") is not consistent with pairing card ',
                                'for pin "',
                                str(p),
                                '".\n')),
                            )
                if score is None:
                    result = None
                else:
                    result = opposite_score[opposite_score[score]]
                card.append(dict(
                    tagger=tagger,
                    notplayed=strm.group('notplayed'),
                    colour=colour,
                    opponent=opponent_pin,
                    score=result))
            swiss_table[pin] = card
            return True

        def get_swiss_pairing_cards(text, tagger):
            spc = text.split()
            if spc[0] in sectiontypes:
                return get_section(text, tagger)
            elif spc[0].lower() == 'source':
                get_source(spc)
                return get_swiss_pairing_cards
            swtr = swiss_table_row.match(text)
            if swtr is None:
                tagger.append_generated_report(
                    self.error,
                    ''.join((
                        '"',
                        text,
                        '" is not recognised as a swiss table row.\n')),
                    )
                self.error_repeat = False
                return get_swiss_pairing_cards
            get_swiss_pairing_card_results(
                swtr.group('pin'),
                swtr.group('row'),
                tagger)
            return get_swiss_pairing_cards

        def add_allplayall_section():
            self.er_pins[self._section] = dict()
            self.er_swiss_table.setdefault(self._section, dict())

        def add_individual_section():
            self.er_players.setdefault(self._section, dict())
            self.er_results.setdefault(
                self._section,
                Section(
                    competition=self._section,
                    games=[]))
        
        def add_fixturelist_section():
            self.er_results.setdefault(self._section, dict())
            self._round = None
            self._date = None
            self._playerlimit = 1

        def add_swiss_section():
            self.er_pins.setdefault(self._section, dict())
            self.er_swiss_table.setdefault(self._section, dict())

        def set_game_processing_rule(text):
            if text == PLAYED_ON:
                self._played_on = PlayedOnStatus.seek_played_on_report
                return True
            if text in COLOUR_RULES:
                self._colourrule = COLOUR_RULES[text]
                return True
            return False

        def split_text_and_pad(text, count, separator=None):
            if separator == None:
                separator = '\t'
            s = text.split(separator, count)
            if len(s) < count + 1:
                s.extend([''] * (count - len(s) + 1))
            return s

        def is_event_name_repeated(text):
            return bool(self.er_name == ' '.join(text.split()))

        def get_source(tokens):
            self.er_source = ' '.join(tokens[1:])

        def nullstring(s):
            if isinstance(s, str):
                return s
            else:
                return ''

        COLOUR_RULES = {
            'whiteonodd':white_on_odd,
            'blackonodd':black_on_odd,
            'whiteonall':white_on_all,
            'blackonall':black_on_all,
            'notspecified':colour_none}

        sectiondata = {
            'allplayall': add_allplayall_section, #individuals
            'league': add_fixturelist_section, #team all play all
            'swiss': add_swiss_section, #individuals
            'fixturelist': add_fixturelist_section, #matches between teams
            'individual': add_individual_section, #games between players
            }
        sectiontypes = {
            'allplayall': get_allplayall_games, #individuals
            'league': get_matches, #team all play all
            'swiss': get_swiss_pairing_cards, #self.GetSwissRounds, #individuals
            'fixturelist': get_matches, #matches between teams
            'individual': get_individual_games, #games between players
            }

        self.textlines = textlines
        state = None
        self._colourrule = colour_none
        self._played_on = PlayedOnStatus.reports_not_played_on
        players = dict()
        self._section = None #latest section name found by get_section
        self._date = None #date in "date" line (get_section sets to None)
        self._round = None #round in "round" line (get_section sets to None)
        self._match = None #latest match name found by get_matches
        self._games = None #board dictionary for games in self._match
        self._match_homeplayers = None
        self._match_awayplayers = None
        self._playerlimit = None

        process = get_event_name

        for linestr, linetag in self.textlines:
            linestr = linestr.strip()
            if len(linestr) == 0:
                continue
            state = process
            process = process(linestr, linetag)

        # hack to spot empty results report
        # Try to get rid of it so self.append_generated_report is not needed.
        if self.er_name is None:
            self.error.append((
                'Results report has too few lines for event name to be present',
                 self))

    # Tagging not used yet so the argument is the text from error, not the key
    # of the item in self._generated_report containing the text (or whatever).
    def get_report_tag_and_text(self, text):#key):
        """"""
        return ('gash', text)#self._generated_report[key])

    
class NullPlayer(Null):

    """Null player placeholder where player name not known.
    """

    def __len__(self):
        return 0

    def __getattr__(self, name):
        return None
    
    def __getitem__(self, i):
        return self

    def is_inconsistent(self, other, problems):
        """Return True if attribute values of self and other are inconsistent.

        Used to check that duplicate reports of a game are consistent allowing
        for previously unknown detail to be added.  Such as the name of a
        player.  Two NullPlayer instances are consistent by definition.

        """
        state = not isinstance(other, self.__class__)
        if state:
            problems.add(NULL_PLAYER)
        return state

    
class PlayedOnStatus():
    """Processing state for game and match reports.

    Normally looking for game and match results where games completed in one
    session.  This is the 'reports_not_played_on' state.

    The 'played_on' command states the following report is for a completed game
    previously reported as unfinished, needind another session or adjudicated,
    or one or more such games in a match.  The command changes the processing
    state to 'seek_played_on_report'.

    A match result received in 'seek_played_on_report' state changes the
    state to 'game_report_played_on'.  Subsequent game reports are
    for completed games previously reported as unfinished until a match report
    is found.
    
    A game result received in 'seek_played_on_report' state changes the state
    to 'reports_not_played_on'
    
    A match result received in 'game_report_played_on' state
    changes the state to 'reports_not_played_on'.
    
    A game result received in 'game_report_played_on' state does
    not change the state.

    """
    reports_not_played_on = 0
    seek_played_on_report = 1
    game_report_played_on = 2