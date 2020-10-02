import json

import torch
import torch.utils.data
from torch import optim
from torch.nn.functional import softmax

from utils.utils import batch_augment
from utils.utils import load_model


def test(data_loader, model, calling_ckp_path, smoking_ckp_path):

    with torch.no_grad():
        optimizer = torch.optim.Adagrad(model.parameters())
        model_calling, _, _, _, _ = load_model(model, optimizer, calling_ckp_path)
        model_smoking, _, _, _, _ = load_model(model, optimizer, smoking_ckp_path)
        model_calling.eval()
        model_smoking.eval()

        threshold = 0.5
        outputs = []

        for i, data in enumerate(data_loader):
            image = data["image"].cuda()
            name = data["name"]

            # y_pred_raw, _, attention_map = model_calling(image)
            # crop_images = batch_augment(image, attention_map, mode='crop', theta=0.1, padding_ratio=0.05)
            # y_pred_crop, _, _ = model_calling(crop_images)
            # output_calling = softmax((y_pred_raw + y_pred_crop) / 2.)

            # y_pred_raw, _, attention_map = model_calling(image)
            # crop_images = batch_augment(image, attention_map, mode='crop', theta=0.1, padding_ratio=0.05)
            # y_pred_crop, _, _ = model_calling(crop_images)
            # output_smoking = softmax((y_pred_raw + y_pred_crop) / 2.)

            output_calling = model_calling(image)
            output_calling = softmax(output_calling, dim=-1)

            output_smoking = model_smoking(image)
            output_smoking = softmax(output_smoking, dim=-1)

            for j in range(image.size(0)):
                if output_calling[j, 1] > threshold and output_smoking[j, 1] > threshold:
                    category = "smoking_calling"
                    score = output_calling[j, 1] * output_smoking[j, 1]
                elif output_calling[j, 1] > threshold:
                    category = "calling"
                    score = output_calling[j, 1]
                elif output_smoking[j, 1] > threshold:
                    category = "smoking"
                    score = output_smoking[j, 1]
                else:
                    category = "normal"
                    score = output_calling[j, 0] * output_smoking[j, 0]

                outputs.append({"name": name[j], "category": category, "score": float(score)})

        with open("./log/result.json", "w+") as f:
            json.dump(outputs, f)
    return 0


# def evaluate(data_loader, model, calling_ckp_path, smoking_ckp_path):
#     with torch.no_grad():
#
#         optimizer = torch.optim.Adagrad(model.parameters())
#         model_calling = load_model(model, optimizer, calling_ckp_path)[0]
#         model_smoking = load_model(model, optimizer, smoking_ckp_path)[0]
#         model_calling.eval()
#         model_smoking.eval()
#         meter = MAP()
#
#         test_loss, correct, total, tp, fp, tn, fn = 0, 0, 0, 0, 0, 0, 0
#         test_loss = 0
#         criterion = torch.nn.CrossEntropyLoss()
#
#         for data in tqdm(data_loader):
#             image = data["image"].cuda()
#             label = data["label"].cuda()
#
#             # call
#             y_pred_raw, _, attention_map = model_calling(image)
#             crop_images = batch_augment(image, attention_map, mode='crop', theta=0.1, padding_ratio=0.05)
#             y_pred_crop, _, _ = model(crop_images)
#             y_pred = (y_pred_raw + y_pred_crop) / 2.
#             loss = criterion(y_pred, label) / 2
#             predict = softmax(y_pred, dim=-1)
#             for i in range(predict.size(0)):
#                 meter.update_calling(predict[i, :], label[i, :])
#
#             # smoke
#             y_pred_raw, _, attention_map = model_smoking(image)
#             crop_images = batch_augment(image, attention_map, mode='crop', theta=0.1, padding_ratio=0.05)
#             y_pred_crop, _, _ = model(crop_images)
#             y_pred = (y_pred_raw + y_pred_crop) / 2.
#             loss += criterion(y_pred, label) / 2
#             test_loss += loss.item() / 2
#             predict = softmax(y_pred, dim=-1)
#             for i in range(predict.size(0)):
#                 meter.update_smoking(predict[i, :], label[i, :])
#
#             _, predict = y_pred.max(1)
#             total += label.size(0)
#             correct += predict.eq(label).sum().item()
#             tp += torch.sum(predict & label)
#             fp += torch.sum(predict & (1 - label))
#             tn += torch.sum((1 - predict) & (1 - label))
#             fn += torch.sum((1 - predict) & label)
#         acc = 100. * correct / total
#         precision = 100.0 * tp / float(tp + fp)
#         recall = 100.0 * tp / float(tp + fn)
#         m_ap = meter.get()
#         print("==> [evaluate] map = {.3f}, loss = {.3f}, acc = {.3f}, precision = {.3f}, recall = {.3f}"
#               .format(m_ap, test_loss, acc, precision, recall))
#     return acc, precision, recall
