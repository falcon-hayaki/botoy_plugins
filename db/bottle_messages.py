''' 漂流瓶 '''
import json
import datetime

class BottleMessagesDB():
    def random_bottle_message(self):
        '''
        随机pop一条漂流瓶信息
        '''
        self.cursor.execute('SELECT * FROM bottle_messages ORDER BY RANDOM() LIMIT 1')
        row = self.cursor.fetchone()

        if row:
            column_names = [description[0] for description in self.cursor.description]
            row_dict = dict(zip(column_names, row))
            self.cursor.execute('DELETE FROM bottle_messages WHERE id = ?', (row_dict['id'],))
            self.conn.commit()
            return row_dict
        else:
            return None