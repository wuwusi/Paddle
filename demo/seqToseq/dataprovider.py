# Copyright (c) 2016 Baidu, Inc. All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from paddle.trainer.PyDataProvider2 import *

UNK_IDX = 2
START = "<s>"
END = "<e>"


def hook(settings, src_dict, trg_dict, file_list, **kwargs):
    # job_mode = 1: training mode
    # job_mode = 0: generating mode
    settings.job_mode = trg_dict is not None
    settings.src_dict = src_dict
    settings.logger.info("src dict len : %d" % (len(settings.src_dict)))
    settings.sample_count = 0

    if settings.job_mode:
        settings.trg_dict = trg_dict
        settings.slots = [
            integer_value(
                len(settings.src_dict),
                seq_type=SequenceType.SEQUENCE), integer_value(
                    len(settings.trg_dict),
                    seq_type=SequenceType.SEQUENCE), integer_value(
                        len(settings.trg_dict),
                        seq_type=SequenceType.SEQUENCE)
        ]
        settings.logger.info("trg dict len : %d" % (len(settings.trg_dict)))
    else:
        settings.slots = [
            integer_value(
                len(settings.src_dict),
                seq_type=SequenceType.SEQUENCE), integer_value(
                    len(open(file_list[0], "r").readlines()),
                    seq_type=SequenceType.SEQUENCE)
        ]


def _get_ids(s, dictionary):
    words = s.strip().split()
    return [dictionary[START]] + \
           [dictionary.get(w, UNK_IDX) for w in words] + \
           [dictionary[END]]


@provider(init_hook=hook, pool_size=50000)
def process(settings, file_name):
    with open(file_name, 'r') as f:
        for line_count, line in enumerate(f):
            line_split = line.strip().split('\t')
            if settings.job_mode and len(line_split) != 2:
                continue
            src_seq = line_split[0]  # one source sequence
            src_ids = _get_ids(src_seq, settings.src_dict)

            if settings.job_mode:
                trg_seq = line_split[1]  # one target sequence
                trg_words = trg_seq.split()
                trg_ids = [settings.trg_dict.get(w, UNK_IDX)
                           for w in trg_words]

                # remove sequence whose length > 80 in training mode
                if len(src_ids) > 80 or len(trg_ids) > 80:
                    continue
                trg_ids_next = trg_ids + [settings.trg_dict[END]]
                trg_ids = [settings.trg_dict[START]] + trg_ids
                yield src_ids, trg_ids, trg_ids_next
            else:
                yield src_ids, [line_count]
