''' 群友语录 '''
import json
import datetime

class Quotes():
    def random_quote(self, from_group: int, user_key: str):
        '''
        随机返回一条语录
        '''
        self.cursor.execute(
            '''
            SELECT * 
            FROM quotes 
            WHERE group_id = {} 
                AND user_key = {}
            ORDER BY RANDOM() LIMIT 1
            '''.format(from_group, user_key)
        )
        row = self.cursor.fetchone()

        if row:
            column_names = [description[0] for description in self.cursor.description]
            row_dict = dict(zip(column_names, row))
            return row_dict
        else:
            return None