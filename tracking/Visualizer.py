from os import makedirs
import sys
from typing import Callable
import numpy as np
from Pinn import PINN
import matplotlib.pyplot as plt
from torch import full_like, save

from simulationSpace.UniformSpace import UniformSpace
from tracking.Plotter import Plotter


class Visualizer:
    def __init__(
        self,
        plotter: Plotter,
        plotSpace: UniformSpace,
        saveDir: str,
        transparent: bool = True,
    ):
        makedirs(saveDir, exist_ok=True)
        self.plotter = plotter
        self.space = plotSpace
        self.saveDir = saveDir
        self.transparent = transparent

    def saveModel(self, model):
        save(model.cpu().state_dict(), self.saveDir + "/model")

    def plotIC(self, initialCondition: Callable):
        x, y, _ = self.space.getInitialPointsKeepDims()
        z = initialCondition(x, y)
        fig = self.plotter.plot(
            z,
            x,
            y,
            self.space.spaceResoultion,
            self.space.spaceResoultion,
            "Initial condition - exact",
        )
        plt.figure(fig)
        plt.savefig(
            self.saveDir + "/initial_condition.png",
            transparent=self.transparent,
        )

    def plotLosses(self, loss_over_time, fileName, labels=[]):
        average_loss = self.__runningAverrage(loss_over_time, window=100)
        fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
        ax.set_title("Loss function (runnig average)")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Loss")
        ax.plot(average_loss, label=labels)
        ax.set_yscale("log")
        if len(labels) > 0:
            plt.legend()
        plt.savefig(
            f"{self.saveDir}/{fileName}", transparent=self.transparent
        )
        plt.close()

    def printLoss(self, losses):
        lossReport = f"""
        Total loss: \t{losses[0]:.5f} ({losses[0]:.3E})
        Interior loss: \t{losses[1]:.5f} ({losses[1]:.3E})
        Initial loss: \t{losses[2]:.5f} ({losses[2]:.3E})
        Bondary loss: \t{losses[3]:.5f} ({losses[3]:.3E})"""
        print(lossReport)

    def printAverageTime(self, time):
        print(f"Averrage epoch time: {time}")

    def animateProgress(self, pinn: PINN, fileName: str):
        frameFileNames = []
        for i in range(self.space.timeResoultion):
            x, y, _ = self.space.getInitialPointsKeepDims()
            timeValue = (
                self.space.timespaceDomain.timeDomain[0]
                + i
                * (
                    self.space.timespaceDomain.timeDomain[1]
                    - self.space.timespaceDomain.timeDomain[0]
                )
                / self.space.timeResoultion
            )
            t = full_like(
                x,
                timeValue,
            )
            z = pinn(x, y, t)
            frameName = self.saveDir + f"/{fileName}_{i}.png"
            fig = self.plotter.plot(
                z,
                x,
                y,
                self.space.spaceResoultion,
                self.space.spaceResoultion,
                f"PINN (t={timeValue:0,.2f})",
            )
            frameFileNames.append(frameName)
            plt.savefig(
                frameName,
                transparent=self.transparent,
                facecolor="white",
            )
            plt.close()
            self.__makeGif(
                frameFileNames=frameFileNames, fileName=fileName
            )

    def __makeGif(self, frameFileNames, fileName):
        try:
            from PIL import Image

            frames = []
            for file in frameFileNames:
                image = Image.open(file)
                frames.append(image)
            frames[0].save(
                self.saveDir + f"/{fileName}.gif",
                format="GIF",
                append_images=frames[1:],
                save_all=True,
                duration=1000,
                loop=0,
            )
        except ImportError:
            print("Can't make gif. PIL not installed")

    def __runningAverrage(self, y, window=100):
        cumsum = np.cumsum(y, axis=0)
        return (cumsum[window:] - cumsum[:-window]) / float(window)
