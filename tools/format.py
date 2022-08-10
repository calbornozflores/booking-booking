import pandas as pd
from config.config import extra_info_substr, rank_description, matchStrField


def formatting():
    """
    Function to give a tabular format to the info initially gathered.
    It uses default input and output file names.
    """
    file = open('output/research.csv', 'r', newline ='')
    lines = file.readlines()
    df_list = []
    for line_list in lines:
        hotelInfo = {}
        line_list = line_list.split(";")[:-1]
        line_list = [ele for ele in line_list if ele != ""]
        line_list = [ele for ele in line_list if not any(ext in ele for ext in extra_info_substr)]
        if len(line_list) > 0:
            hotelInfo["hotel_name"] = line_list[0]
            try:
                rankDescriptionField = [x for x in line_list if any(rd in x for rd in rank_description)][0]
                if any(c.isdigit() for c in rankDescriptionField):
                    rankDesciption, rankNumber = rankDescriptionField.split(" ")
                    hotelInfo["rank_description"] = rankDesciption
                    try:
                        hotelInfo["rank_value"] = float(rankNumber)
                    except:
                        pass
                else:
                    try:
                        hotelInfo["rank_description"] = rankDescriptionField
                        hotelInfo["rank_value"] = float(line_list[ line_list.index(rankDescriptionField) - 1 ])
                    except:
                        pass
            except:
                pass
            for k in matchStrField.keys():
                try:
                    xField = [x for [i, x] in enumerate(line_list) if k in x][0]
                    hotelInfo[matchStrField[k]] = xField
                    if k == "taxes":
                        hotelInfo["price"] = line_list[line_list.index(xField) - 1]
                except:
                    pass
            df_list.append(hotelInfo)
    hotel_df = pd.DataFrame(df_list)
    hotel_df["taxes"] = hotel_df["taxes"].str.extract(r'([1-9]+,[0-9]+)')
    hotel_df["price"] = hotel_df["price"].str.split(" ").str[-1]
    hotel_df["reviews"] = hotel_df["reviews"].str.replace(",", "").str.extract(r'(\d+)')
    file.close()
    hotel_df.to_csv("output/research_table.csv", index = False)

