''' 漂流瓶 '''
import json
import datetime

class BottleMessagesDB():
    def random_bottle_message(self, from_group: int, from_user: int):
        '''
        随机pop一条漂流瓶信息
        排除来自同一群或同一用户扔出的漂流瓶
        '''
        self.cursor.execute(
            '''
            SELECT * 
            FROM bottle_messages 
            WHERE group_id != {} 
                AND user_id != {}
            ORDER BY RANDOM() LIMIT 1
            '''.format(from_group, from_user)
        )
        row = self.cursor.fetchone()

        if row:
            column_names = [description[0] for description in self.cursor.description]
            row_dict = dict(zip(column_names, row))
            self.cursor.execute('DELETE FROM bottle_messages WHERE id = ?', (row_dict['id'],))
            self.conn.commit()
            return row_dict
        else:
            return None